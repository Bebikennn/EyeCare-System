"""
Clean up old sample ML metrics and keep only real trained model metrics
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app
from database import db, MLMetrics

def cleanup_old_metrics():
    """Remove old sample metrics, keep only real trained models"""
    with app.app_context():
        print("=" * 60)
        print("Cleaning Up Old ML Metrics")
        print("=" * 60)
        
        # Get all metrics
        all_metrics = MLMetrics.query.order_by(MLMetrics.training_date.desc()).all()
        
        print(f"\n📊 Found {len(all_metrics)} metric records:")
        print()
        
        for i, metric in enumerate(all_metrics, 1):
            print(f"{i}. Model: {metric.model_version}")
            print(f"   Accuracy: {metric.accuracy:.4f} ({metric.accuracy*100:.2f}%)")
            print(f"   Dataset: {metric.dataset_size} samples")
            print(f"   Date: {metric.training_date}")
            print()
        
        # Find old sample metrics (accuracy < 0.95 or dataset_size < 100)
        old_metrics = [
            m for m in all_metrics 
            if m.accuracy < 0.95 or m.dataset_size < 100
        ]
        
        if not old_metrics:
            print("✓ No old sample metrics found. Database is clean!")
            return
        
        print(f"🗑️  Found {len(old_metrics)} old sample metrics to delete:")
        for metric in old_metrics:
            print(f"   - {metric.model_version} (Accuracy: {metric.accuracy:.4f}, Dataset: {metric.dataset_size})")
        
        print()
        response = input("Delete these old metrics? (yes/no): ")
        
        if response.lower() in ['yes', 'y']:
            for metric in old_metrics:
                db.session.delete(metric)
            
            db.session.commit()
            print(f"\n✓ Deleted {len(old_metrics)} old metric records")
            
            # Show remaining metrics
            remaining = MLMetrics.query.order_by(MLMetrics.training_date.desc()).all()
            print(f"\n📊 Remaining metrics: {len(remaining)}")
            for metric in remaining:
                print(f"   ✓ {metric.model_version} - {metric.accuracy*100:.2f}% - {metric.dataset_size} samples")
        else:
            print("\n❌ Cleanup cancelled")

if __name__ == "__main__":
    cleanup_old_metrics()
