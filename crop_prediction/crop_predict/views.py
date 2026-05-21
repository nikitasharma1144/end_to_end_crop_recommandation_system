from pathlib import Path
import pickle

from django.shortcuts import render
from django.http import HttpResponse

# load prediction model from the workspace, if available
MODEL_PATH = Path(__file__).resolve().parent.parent.parent / 'end_to_end_crop_recommandation_system' / 'random_forest_model.pkl'
model = None
if MODEL_PATH.exists():
    try:
        with open(MODEL_PATH, 'rb') as model_file:
            model = pickle.load(model_file)
    except Exception:
        model = None


def home(request):
    return render(request, 'index.html')


def predict(request):
    if request.method != 'POST':
        return HttpResponse('Only POST method is allowed', status=405)

    try:
        nitrogen = float(request.POST.get('Nitrogen', 0))
        phosphorous = float(request.POST.get('Phosphorous', 0))
        potassium = float(request.POST.get('Potassium', 0))
        temperature = float(request.POST.get('Temperature', 0))
        humidity = float(request.POST.get('Humidity', 0))
        rainfall = float(request.POST.get('Rainfall', 0))
        ph = float(request.POST.get('Ph', 0))
    except (TypeError, ValueError):
        return HttpResponse('Invalid input values', status=400)

    if model is None:
        return HttpResponse('Prediction model is not loaded. Place random_forest_model.pkl in the workspace and restart the server.', status=500)

    try:
        result = model.predict([[nitrogen, phosphorous, potassium, temperature, humidity, rainfall, ph]])
    except Exception as e:
        return HttpResponse(f'Prediction failed: {e}', status=500)

    if hasattr(result, '__iter__'):
        result_value = result[0]
    else:
        result_value = result

    return render(request, 'result.html', {'result': result_value})


    
