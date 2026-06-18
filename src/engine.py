import numpy as np
import pandas as pd

class CyberDNAEngine:
    @staticmethod
    def calculate_bsi(dbs_a, dbs_b):
        """
        Calculates the Behavioral Similarity Index (BSI) using Cosine Similarity.
        BSI ranges from 0 (completely dissimilar) to 1 (completely identical).
        """
        dot_product = np.dot(dbs_a, dbs_b)
        norm_a = np.linalg.norm(dbs_a)
        norm_b = np.linalg.norm(dbs_b)
        
        if norm_a == 0 or norm_b == 0:
            return 0.0
            
        bsi = dot_product / (norm_a * norm_b)
        return float(bsi)

    @staticmethod
    def calculate_bds(dbs_t1, dbs_t2):
        """
        Calculates the Behavioral Drift Score (BDS) using Euclidean Distance.
        BDS measures how much a single user's behavioral vector shifts over time.
        """
        bds = np.linalg.norm(dbs_t1 - dbs_t2)
        return float(bds)

class DepartmentalFilter:
    def __init__(self, signatures, ldap_df):
        """
        signatures: dict mapping user -> { week -> dbs_vector }
        ldap_df: DataFrame mapping 'user' to 'department'
        """
        self.signatures = signatures
        # Map user to department
        self.user_dept = dict(zip(ldap_df['user'], ldap_df['department']))
        self.departments = ldap_df['department'].unique()
        
        self.centroids = {} # (dept, week) -> centroid_vector
        self.cohesion = {}  # (dept, week) -> (mean_bsi, std_bsi)
        
        self._compute_centroids()
        self._compute_cohesion()
        
    def _compute_centroids(self):
        """
        Calculates the average DBS vector (centroid) for each department per week.
        """
        # Group users by department
        dept_users = {}
        for user, dept in self.user_dept.items():
            if dept not in dept_users:
                dept_users[dept] = []
            dept_users[dept].append(user)
            
        # Determine all weeks in dataset
        all_weeks = set()
        for user, weeks in self.signatures.items():
            all_weeks.update(weeks.keys())
            
        # Compute weekly centroids
        for dept in self.departments:
            users_in_dept = dept_users.get(dept, [])
            if not users_in_dept:
                continue
                
            for week in all_weeks:
                vectors = []
                for user in users_in_dept:
                    if user in self.signatures and week in self.signatures[user]:
                        vectors.append(self.signatures[user][week])
                        
                if vectors:
                    self.centroids[(dept, week)] = np.mean(vectors, axis=0)
                    
    def _compute_cohesion(self):
        """
        Calculates the within-department BSI mean and standard deviation (cohesion)
        for Z-score thresholding.
        """
        dept_users = {}
        for user, dept in self.user_dept.items():
            if dept not in dept_users:
                dept_users[dept] = []
            dept_users[dept].append(user)
            
        for (dept, week), centroid in self.centroids.items():
            users_in_dept = dept_users.get(dept, [])
            similarities = []
            
            for user in users_in_dept:
                if user in self.signatures and week in self.signatures[user]:
                    vector = self.signatures[user][week]
                    bsi = CyberDNAEngine.calculate_bsi(vector, centroid)
                    similarities.append(bsi)
                    
            if similarities:
                mean_bsi = np.mean(similarities)
                std_bsi = np.std(similarities)
                # Avoid std of 0 if only 1 user or all identical
                if std_bsi == 0:
                    std_bsi = 0.01
                self.cohesion[(dept, week)] = (mean_bsi, std_bsi)

    def check_role_transition(self, user, target_week, old_dept, z_threshold=-2.5):
        """
        Evaluates a user's signature in target_week against other departments' centroids.
        Uses adaptive Z-score gating.
        Returns (is_transition, new_department, bsi_score)
        """
        if user not in self.signatures or target_week not in self.signatures[user]:
            return False, None, 0.0
            
        vector = self.signatures[user][target_week]
        best_match = None
        best_bsi = 0.0
        
        # Compare to all other departments
        for dept in self.departments:
            if dept == old_dept:
                continue
                
            centroid_key = (dept, target_week)
            cohesion_key = (dept, target_week)
            
            if centroid_key in self.centroids and cohesion_key in self.cohesion:
                centroid = self.centroids[centroid_key]
                mean_bsi, std_bsi = self.cohesion[cohesion_key]
                
                bsi = CyberDNAEngine.calculate_bsi(vector, centroid)
                z_score = (bsi - mean_bsi) / std_bsi
                
                # Z-score gating check: within the department's normal profile distribution
                if z_score >= z_threshold:
                    if bsi > best_bsi:
                        best_bsi = bsi
                        best_match = dept
                        
        if best_match is not None and best_bsi > 0.85: # Require a baseline resemblance
            return True, best_match, best_bsi
            
        return False, None, 0.0
