FROM ghcr.io/ad-sdl/madsci:latest

LABEL org.opencontainers.image.source=https://github.com/AD-SDL/vention_rail_module
LABEL org.opencontainers.image.description="Drivers and REST API's for the Vention Linear Rail"
LABEL org.opencontainers.image.licenses=MIT

#########################################
# Module specific logic goes below here #
#########################################

RUN mkdir -p vention_rail_module

COPY ./src vention_rail_module/src
COPY ./README.md vention_rail_module/README.md
COPY ./pyproject.toml vention_rail_module/pyproject.toml

RUN --mount=type=cache,target=/root/.cache \
    pip install -e ./vention_rail_module

CMD ["python", "vention_rail_module/src/rail_rest_node.py"]

#########################################
