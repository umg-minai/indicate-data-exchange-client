import logging

from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import HTMLResponse, JSONResponse
from starlette.routing import Route, Mount
from starlette.staticfiles import StaticFiles
from starlette.templating import Jinja2Templates

from indicate_data_exchange_client.config.configuration import Configuration
from indicate_data_exchange_client.logic import State

logger = logging.getLogger("web")


# Setup Jinja2 templates
templates = Jinja2Templates(directory="indicate_data_exchange_client/templates")


# API endpoints for other components

def trigger(state: State):
    async def trigger_closure(request: Request):
        """Trigger the collection of results for review."""
        try:
            state.fetch_results()
            return JSONResponse({
                "success": True,
                "message": "Results fetched successfully"
            })
        except Exception as e:
            logger.error(f"Failed to fetch results from database: {e}")
            return JSONResponse(
                {"error": f"Failed to fetch results: {str(e)}"},
                status_code=500
            )
    return trigger_closure

# API endpoints for Javascript frontend

def confirm_upload(state: State):
    async def confirm_upload_closure(request: Request):
        """Handle confirmation and upload of result."""
        if state.results is None:
            return JSONResponse(
                {"error": "No results pending review"},
                status_code=400
            )
        else:
            try:
                state.transmit_results()
                return JSONResponse({
                    "success": True,
                    "message": "Results uploaded successfully"
                })
            except Exception as e:
                logger.error(f"Upload failed: {e}")
                return JSONResponse(
                    {"error": f"Upload failed: {str(e)}"},
                    status_code=500
                )
    return confirm_upload_closure

def reject_upload(state: State):
    async def reject_upload_closure(request: Request):
        """Handle rejection of pending results."""
        if state.results is None:
            return JSONResponse(
                {"error": "No results pending review"},
                status_code=400
            )
        else:
            state.clear_results()
            return JSONResponse({
                "success": True,
                "message": "Results rejected and cleared"
            })
    return reject_upload_closure

# Pages

def review_page(configuration: Configuration, state: State):
    async def review_page_closure(request: Request):
        """Display the review page with data pending confirmation."""
        # Transform the results into dict objects for use in
        # templates. Collect some statistics that will also be
        # displayed by the templates along the way.
        data = None
        if state.results is not None:
            results = state.results
            # Populate indicator information dictionary from meta
            # data, if available.
            indicator_infos = {}
            meta_data = state.meta_data
            if meta_data is not None:
                for indicator_info in meta_data.info:
                    indicator_id = indicator_info.indicator_id
                    title = indicator_info.title
                    indicator_infos[indicator_id] = {"usable": 0, "unusable": 0, "title": title}
            # Put results into rows of usable results and unsuable
            # results. Include the quality indicator title as label,
            # if available. Also track overall temporal period from
            # which results have been computed and result counts for
            # each quality indicator.
            period_start, period_end = None, None
            usable_rows, unusable_rows = [], []
            def transform_results(results, into, is_usable=True):
                nonlocal period_start, period_end
                for result in results:
                    indicator_id = result.indicator_id
                    info = indicator_infos.get(indicator_id, { "usable": 0, "unusable": 0 })
                    indicator_infos[indicator_id] = info

                    label = info["title"] if "title" in info else str(indicator_id)
                    result_start = result.period_start
                    result_end = result.period_end
                    into.append({
                        "indicator":          label,
                        "aggregation_period": result.period_kind,
                        "period_start":       result_start.isoformat(),
                        "period_end":         result_end.isoformat(),
                        "average_value":      float(result.average_value),
                        "observation_count":  result.observation_count,
                    })

                    if is_usable:
                        period_start = min(period_start, result_start) if period_start is not None else result_start
                        period_end = max(period_end, result_end) if period_end is not None else result_end
                        info["usable"] += 1
                    else:
                        info["unusable"] += 1
            transform_results(results.usable_results, usable_rows)
            transform_results(results.unusable_results, unusable_rows, is_usable=False)
            data = {
                "computed_at":      results.computed_at,
                "period_start":     period_start,
                "period_end":       period_end,
                "indicator_counts": [ { "id": indicator_id, **info }
                                      for indicator_id, info in indicator_infos.items()],
                "usable_results":   usable_rows,
                "unusable_results": unusable_rows,
            }

        return HTMLResponse(
            templates.TemplateResponse(
                request,
                "review.html",
                context={
                    "provider_id":            configuration.provider_id,
                    "data_exchange_endpoint": configuration.data_exchange.endpoint,
                    "data":                   data,
                }
            ).body
        )
    return review_page_closure

# Create the Starlette application

def make_app(configuration: Configuration, state: State):
    review_page_closure = review_page(configuration, state)
    routes = [
        # API for other components
        Route("/api/trigger", endpoint=trigger(state), methods=["POST"]),
        # API for frontend Javascript
        Route("/api/confirm", endpoint=confirm_upload(state), methods=["POST"]),
        Route("/api/reject", endpoint=reject_upload(state), methods=["POST"]),
        # Pages and static content
        Mount('/static', StaticFiles(directory='static'), name='static'),
        Route("/review", endpoint=review_page_closure, methods=["GET"]),
        Route("/", endpoint=review_page_closure, methods=["GET"]),
    ]
    return Starlette(routes=routes)
