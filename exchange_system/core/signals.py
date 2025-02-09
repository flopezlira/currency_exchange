import logging

from django.db.models.signals import post_save
from django.dispatch import receiver

from core.adapters import reload_providers
from core.models import Provider

# Set up a logger for the core module
logger = logging.getLogger("core")

# Define a signal receiver function that listens for the post_save signal on the Provider model
@receiver(post_save, sender=Provider)
def auto_reload_providers(sender, instance, **kwargs):
    """
    Signal receiver that automatically reloads providers when a Provider instance is saved.

    This function is triggered after a Provider instance is saved (either created or updated).
    It logs the modification and calls the reload_providers function to refresh the provider data.

    Args:
        sender (Model): The model class that sent the signal.
        instance (Provider): The actual instance being saved.
        **kwargs: Additional keyword arguments.
    """
    # Log the modification of the provider instance
    logger.info(f"Provider {instance.name} was modified. Reloading providers...")
    
    # Call the function to reload providers
    reload_providers()
