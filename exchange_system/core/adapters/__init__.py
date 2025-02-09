from core.models import Provider
import importlib
import logging

logger = logging.getLogger("core")

def load_adapter(provider):
    """
    Dynamically loads the adapter for a given provider.
    """
    logger.info(f"Loading adapter for provider {provider.name}")
    try:
        module_path, class_name = provider.adapter_path.rsplit(".", 1)
        module = importlib.import_module(f"{module_path}")
        adapter_class = getattr(module, class_name)
        return adapter_class(provider)
    except ModuleNotFoundError:
        logger.error(f"Module {module_path} not found for provider {provider.name}.")
    except AttributeError:
        logger.error(f"Class {class_name} not found in {module_path}.")
    except Exception as e:
        logger.error(f"Unexpected error loading adapter for provider {provider.name}: {e}")

    return None

def reload_providers():
    """
    Reloads all active providers from the database and initializes their adapters.

    :return: Dictionary of active provider name -> adapter instance.
    """
    logger.info("Reloading providers")
    providers = Provider.objects.filter(active=True)
    adapters = {}

    for provider in providers:
        adapter = load_adapter(provider)
        if adapter:
            adapters[provider.name] = adapter
            logger.info(f"Loaded adapter for provider {provider.name}")

    return adapters
