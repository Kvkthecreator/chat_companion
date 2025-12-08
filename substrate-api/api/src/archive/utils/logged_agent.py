from functools import wraps

from src.utils.event_log import log_event


def logged(agent_name: str):
    def decorator(fn):
        @wraps(fn)
        async def wrapper(*args, **kwargs):
            basket_id = kwargs.get("basket_id") or getattr(args[0], "basket_id", None)
            await log_event(
                basket_id=basket_id,
                agent=agent_name,
                phase="start",
                payload=kwargs,
            )
            try:
                result = await fn(*args, **kwargs)
                await log_event(
                    basket_id=basket_id,
                    agent=agent_name,
                    phase="success",
                    payload=result,
                )
                return result
            except Exception as e:
                await log_event(
                    basket_id=basket_id,
                    agent=agent_name,
                    phase="error",
                    payload={"error": str(e)},
                )
                raise

        return wrapper

    return decorator
