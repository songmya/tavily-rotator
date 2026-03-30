import express from "express";
import { z } from "zod";
import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { StreamableHTTPServerTransport } from "@modelcontextprotocol/sdk/server/streamableHttp.js";

const PORT = process.env.PORT || 9000;
const GATEWAY_BASE_URL = process.env.GATEWAY_BASE_URL || "http://nas-tavily-gateway:8000";
const GATEWAY_TOKEN = process.env.GATEWAY_TOKEN || "";

function buildServer() {
  const server = new McpServer({
    name: "nas-tavily-mcp",
    version: "1.0.0",
  });

  server.tool(
    "tavily-search",
    {
      query: z.string(),
      topic: z.enum(["general", "news", "finance"]).optional(),
      search_depth: z.enum(["basic", "advanced", "fast", "ultra-fast"]).optional(),
      max_results: z.number().int().min(1).max(20).optional(),
      include_answer: z.boolean().optional(),
      include_raw_content: z.boolean().optional(),
      include_images: z.boolean().optional(),
      include_image_descriptions: z.boolean().optional(),
      include_domains: z.array(z.string()).optional(),
      exclude_domains: z.array(z.string()).optional(),
      time_range: z.enum(["day", "week", "month", "year", "d", "w", "m", "y"]).optional(),
      country: z.string().optional(),
      chunks_per_source: z.number().int().min(1).max(3).optional(),
    },
    async (args) => {
      const resp = await fetch(`${GATEWAY_BASE_URL}/search`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-Api-Key": GATEWAY_TOKEN,
        },
        body: JSON.stringify(args),
      });

      const text = await resp.text();

      if (!resp.ok) {
        return {
          content: [
            {
              type: "text",
              text: `Gateway 调用失败: HTTP ${resp.status}\n${text}`,
            },
          ],
        };
      }

      return {
        content: [
          {
            type: "text",
            text: text,
          },
        ],
      };
    }
  );

  return server;
}

const app = express();
app.use(express.json());

app.get("/health", (_req, res) => {
  res.json({ ok: true, service: "nas-tavily-mcp" });
});

app.all("/mcp", async (req, res) => {
  try {
    const transport = new StreamableHTTPServerTransport({
      sessionIdGenerator: undefined,
    });

    const server = buildServer();
    await server.connect(transport);
    await transport.handleRequest(req, res, req.body);
  } catch (err) {
    console.error("MCP request error:", err);
    res.status(500).json({
      error: "mcp_server_error",
      detail: String(err),
    });
  }
});

app.listen(PORT, () => {
  console.log(`nas-tavily-mcp listening on port ${PORT}`);
});
``