from queue import Queue
from config.models import MODELS
import psutil

MIN_AVAILABLE_MEMORY_PERCENT = 20.0
MIN_AVAILABLE_CPU_CORES = 2

def model_memory_limits(runningModels: dict, upcomingModels: dict, available: float, total: float):
    limits = {}
    percent = (available/total)*100

    stop = percent < MIN_AVAILABLE_MEMORY_PERCENT

    for size in upcomingModels:
        runningModels[size] = 1

    models = runningModels.keys() if stop else [size for size in upcomingModels if size not in runningModels]
    models = [MODELS[size] for size in models if size in MODELS]
    models.sort(key=lambda model: model['initialMemoryUsage'], reverse=stop)

    freed = 0
    sign = 1 if stop else -1
    for model in models:
        freed += sign*model['initialMemoryUsage']
        modelPercent = ((available + freed)/total)*100
        limits[model['rows']] = sign
        if modelPercent < MIN_AVAILABLE_MEMORY_PERCENT:
            sign = 0

    return limits

def workers_core_limit(cpus: list[float]):
    availableCores = int(len(cpus) - sum(cpus)/100.00)
    return MIN_AVAILABLE_CPU_CORES - availableCores

def monitor(runningModels: dict={}, upcomingModels: dict={}, averageTimeQueue: Queue=None) -> dict[str, int]:
    virtualMem = psutil.virtual_memory()
    total = virtualMem.total
    available = virtualMem.available
    percent = int((available/total)*100)
    memoryLimits = model_memory_limits(runningModels.copy(), upcomingModels, available, total)

    coreLimit = workers_core_limit(psutil.cpu_percent(percpu=True))

    return {
        'free': percent,
        'low': percent < MIN_AVAILABLE_MEMORY_PERCENT,
        'memory': memoryLimits,
        'cpu': coreLimit
    }

    
                
        

