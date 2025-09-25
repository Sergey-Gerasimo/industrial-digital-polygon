from .settings import settings
from .log_settings import app_logger, LoggerConfig

SETTINGS_IS_LOAD = False

if not SETTINGS_IS_LOAD:
    SETTINGS_IS_LOAD = True
    LoggerConfig.configure(
        log_level=settings.log.log_level,
        log_format=settings.log.log_format,
        debug=settings.log.debug,
    )

    settings.validate_default_values(logger=app_logger)
    app_logger.debug("Settings loaded:\n{}", settings.model_dump())


__all__ = [
    "settings",
    "app_logger",
]
