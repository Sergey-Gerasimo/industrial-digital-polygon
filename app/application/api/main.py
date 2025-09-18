from fastapi import FastAPI


def create_app():
    return FastAPI(
        title="Industrial-Digital-Polygon",
        docs_url="/api/docs",
        description="Цифровой полигон: где станки общаются JSON'ом, а сменный мастер требует 'сделать красиво'",
    )
