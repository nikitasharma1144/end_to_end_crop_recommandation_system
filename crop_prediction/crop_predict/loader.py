import os
import pickle
from functools import lru_cache
from django.conf import settings

# 1. This function wakes up the model from the safe
@lru_cache(maxsize=1)  # Keeps the model in server memory so it stays lightning fast!
def load_bundle():
    # Automatically finds the exact absolute path to your pickle file on your computer
    pickle_path = os.path.join(settings.BASE_DIR, 'crop_predict', 'crop_recommendation_rf.pkl')
    
    # Opens the file in Read-Binary ('rb') mode
    with open(pickle_path, 'rb') as f:
        bundle = pickle.load(f)  # This is the deserialization step!
    
    # Simple check to make sure the model data isn't corrupted
    assert 'model' in bundle and 'feature_cols' in bundle, "Invalid model bundle structure!"
    return bundle


# 2. This function takes user inputs, structures them, and runs the calculation
def predict_one(feature_dict):
    # Call the loader function above to grab the active model bundle
    bundle = load_bundle()
    
    model = bundle['model']
    feature_columns = bundle['feature_cols']
    
    # Takes the raw user form inputs and organizes them into the mathematically correct order
    # Example: Arranges [N, P, K, Temp...] perfectly into a 2D array matrix
    x = [[float(feature_dict[c]) for c in feature_columns]]
    
    # Feeds the organized data matrix to the model to get the prediction
    prediction = model.predict(x)
    
    # Returns the clean string answer (e.g., 'rice') back to your Django view
    
    return prediction[0]
