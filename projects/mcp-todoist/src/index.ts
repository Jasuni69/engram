import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import {
  CallToolRequestSchema,
  ListToolsRequestSchema,
} from "@modelcontextprotocol/sdk/types.js";

const API_TOKEN = process.env.TODOIST_API_TOKEN;
if (!API_TOKEN) throw new Error("TODOIST_API_TOKEN env var is required");

const BASE = "https://api.todoist.com/api/v1";

async function api(method: string, path: string, body?: unknown) {
  const res = await fetch(`${BASE}${path}`, {
    method,
    headers: {
      Authorization: `Bearer ${API_TOKEN}`,
      "Content-Type": "application/json",
    },
    body: body ? JSON.stringify(body) : undefined,
  });
  if (!res.ok) throw new Error(`Todoist API error: ${res.status} ${await res.text()}`);
  if (res.status === 204) return null;
  return res.json();
}

const server = new Server(
  { name: "mcp-todoist", version: "1.0.0" },
  { capabilities: { tools: {} } }
);

server.setRequestHandler(ListToolsRequestSchema, async () => ({
  tools: [
    {
      name: "get_tasks",
      description: "Get all active tasks, optionally filtered by project",
      inputSchema: {
        type: "object",
        properties: {
          project_id: { type: "string", description: "Filter by project ID (optional)" },
        },
      },
    },
    {
      name: "create_task",
      description: "Create a new task",
      inputSchema: {
        type: "object",
        properties: {
          content: { type: "string", description: "Task title" },
          description: { type: "string" },
          due_string: { type: "string", description: "e.g. 'tomorrow', 'next monday'" },
          priority: { type: "number", minimum: 1, maximum: 4, description: "1-4 (4=urgent)" },
          project_id: { type: "string" },
        },
        required: ["content"],
      },
    },
    {
      name: "complete_task",
      description: "Mark a task as complete",
      inputSchema: {
        type: "object",
        properties: { task_id: { type: "string" } },
        required: ["task_id"],
      },
    },
    {
      name: "delete_task",
      description: "Delete a task",
      inputSchema: {
        type: "object",
        properties: { task_id: { type: "string" } },
        required: ["task_id"],
      },
    },
    {
      name: "get_projects",
      description: "List all projects",
      inputSchema: { type: "object", properties: {} },
    },
  ],
}));

server.setRequestHandler(CallToolRequestSchema, async (request) => {
  const { name, arguments: args } = request.params;
  try {
    switch (name) {
      case "get_tasks": {
        const qs = args?.project_id ? `?project_id=${args.project_id}` : "";
        const tasks = await api("GET", `/tasks${qs}`);
        return { content: [{ type: "text", text: JSON.stringify(tasks, null, 2) }] };
      }
      case "create_task": {
        const task = await api("POST", "/tasks", {
          content: args!.content,
          description: args?.description,
          due_string: args?.due_string,
          priority: args?.priority,
          project_id: args?.project_id,
        });
        return { content: [{ type: "text", text: `Created: ${(task as any).id} — ${(task as any).content}` }] };
      }
      case "complete_task": {
        await api("POST", `/tasks/${args!.task_id}/close`);
        return { content: [{ type: "text", text: `Task ${args!.task_id} completed.` }] };
      }
      case "delete_task": {
        await api("DELETE", `/tasks/${args!.task_id}`);
        return { content: [{ type: "text", text: `Task ${args!.task_id} deleted.` }] };
      }
      case "get_projects": {
        const projects = await api("GET", "/projects");
        return { content: [{ type: "text", text: JSON.stringify(projects, null, 2) }] };
      }
      default:
        throw new Error(`Unknown tool: ${name}`);
    }
  } catch (err) {
    return { content: [{ type: "text", text: `Error: ${(err as Error).message}` }], isError: true };
  }
});

const transport = new StdioServerTransport();
await server.connect(transport);
