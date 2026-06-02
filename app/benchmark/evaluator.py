from typing import List, Dict, Any

class TextToSQLEvaluator:
    @staticmethod
    def calculate_exact_match(predicted_sql: str, ground_truth_sql: str) -> bool:
        """
        Compares query structures (ignoring minor formatting details like spaces and casing).
        """
        if not predicted_sql or not ground_truth_sql:
            return False
            
        p_norm = " ".join(predicted_sql.lower().strip().split())
        g_norm = " ".join(ground_truth_sql.lower().strip().split())
        
        # Strip trailing semicolons
        if p_norm.endswith(";"):
            p_norm = p_norm[:-1]
        if g_norm.endswith(";"):
            g_norm = g_norm[:-1]
            
        return p_norm == g_norm

    def evaluate_dataset(self, predictions: List[Dict[str, str]]) -> Dict[str, Any]:
        """
        Evaluates a list of predictions containing:
        [{"predicted_sql": "...", "ground_truth_sql": "..."}]
        Returns performance metrics.
        """
        total = len(predictions)
        if total == 0:
            return {"accuracy": 0.0, "exact_matches": 0, "total": 0}

        matches = 0
        for pred in predictions:
            if self.calculate_exact_match(pred.get("predicted_sql", ""), pred.get("ground_truth_sql", "")):
                matches += 1

        accuracy = (matches / total) * 100
        return {
            "accuracy": round(accuracy, 2),
            "exact_matches": matches,
            "total": total
        }