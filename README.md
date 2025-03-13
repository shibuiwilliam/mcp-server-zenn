# mcp-server-zenn: Unofficial MCP server for Zenn (https://zenn.dev/)

## Overview

This is an unofficial Model Context Protocol server for [Zenn](https://zenn.dev/). Build on top of [Zenn's dev API](https://zenn.dev/api/).

## Features

- Fetch a list of articles
- Fetch a list of books

## Run this project locally

This project is not yet set up for ephemeral environments (e.g. `uvx` usage). Run this project locally by cloning this repo:

```shell
git clone https://github.com/shibuiwilliam/mcp-server-zenn.git
```

You can launch the [MCP inspector](https://github.com/modelcontextprotocol/inspector) via [npm](https://docs.npmjs.com/downloading-and-installing-node-js-and-npm):

```shell
npx @modelcontextprotocol/inspector uv --directory=src/mcp_server_zenn run mcp-server-zenn
```

Upon launching, the Inspector will display a URL that you can access in your browser to begin debugging.


OR
Add this tool as a MCP server:

```json
{
  "zenn": {
    "command": "uv",
    "args": [
      "--directory",
      "/path/to/mcp-server-zenn",
      "run",
      "mcp-server-zenn"
    ]
  }
}
```

## Deployment

(TODO)

## [License](./LICENSE)


