from fastapi import Request


async def get_request_context(request: Request) -> dict:
    context = {}
    context["query"] = dict(request.query_params)
    context["headers"] = dict(request.headers)
    context["path"] = request.path_params
    context["method"] = request.method
    context["url"] = str(request.url)

    if await request.body():
        context["body"] = await request.json()

    return context
