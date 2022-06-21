from queue import Queue
from config.models import MODELS
import psutil

MIN_AVAILABLE_MEMORY_PERCENT = 20.0
MAX_AVAILABLE_MEMORY_PERCENT = 25.0
MIN_AVAILABLE_CPU_CORES = 2

def model_memory_limits(runningModels: list[int], upcomingModels: list[int], available: float, total: float):
    limits = {}
    percent = (available/total)*100
    print(f"Memory available percent: {percent}")
    if percent < MIN_AVAILABLE_MEMORY_PERCENT or percent > MAX_AVAILABLE_MEMORY_PERCENT:

        stop = percent < MIN_AVAILABLE_MEMORY_PERCENT

        models = runningModels if stop else upcomingModels
        models = [MODELS[model] for model in models]
        models.sort(key=lambda model: model['initialMemoryUsage'], reverse=stop)

        for model in models:
            free = available + (1 if stop else -1)*model['initialMemoryUsage']
            modelPercent = (free/total)*100
            print(f"modelPercent: {modelPercent}, percent: {percent}")
            if modelPercent < MIN_AVAILABLE_MEMORY_PERCENT or modelPercent > MAX_AVAILABLE_MEMORY_PERCENT:
                limits[model['rows']] = (1 if stop else -1)
                break

    return limits

def workers_core_limit(cpus: list[float]):
    availableCores = int(len(cpus) - sum(cpus)/100.00)
    return MIN_AVAILABLE_CPU_CORES - availableCores 

def monitor(runningModels: list[int]={}, upcomingModels: list[int]={}, averageTimeQueue: Queue=None) -> dict[str, int]:
    virtualMem = psutil.virtual_memory()
    memoryLimits = model_memory_limits(runningModels, upcomingModels, virtualMem.available, virtualMem.total)

    coreLimit = workers_core_limit(psutil.cpu_percent(percpu=True))

    return {
        'memory': memoryLimits,
        'cpu': coreLimit
    }

    
                
        

