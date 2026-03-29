import express, { type Express, type Request, type Response } from "express";
import cors from "cors";
import pinoHttp from "pino-http";
import { createProxyMiddleware } from "http-proxy-middleware";
import router from "./routes";
import { logger } from "./lib/logger";

const PYTHON_BACKEND = "http://localhost:8000";

let pythonReady = false;

async function checkPythonHealth(): Promise<boolean> {
  try {
    const resp = await fetch(`${PYTHON_BACKEND}/api/health`);
    return resp.ok;
  } catch {
    return false;
  }
}

async function waitForPython(maxWaitMs = 180000): Promise<void> {
  const start = Date.now();
  while (Date.now() - start < maxWaitMs) {
    if (await checkPythonHealth()) {
      pythonReady = true;
      logger.info("Python backend is ready");
      return;
    }
    logger.info(
      { elapsed: Math.round((Date.now() - start) / 1000) },
      "Waiting for Python backend...",
    );
    await new Promise((r) => setTimeout(r, 3000));
  }
  logger.warn(
    "Python backend did not become ready within timeout, will keep trying in background",
  );
  backgroundHealthCheck();
}

async function backgroundHealthCheck(): Promise<void> {
  while (!pythonReady) {
    await new Promise((r) => setTimeout(r, 5000));
    if (await checkPythonHealth()) {
      pythonReady = true;
      logger.info("Python backend is now ready (background check)");
      return;
    }
  }
}

if (process.env["NODE_ENV"] === "production") {
  waitForPython();
}

const pythonProxy = createProxyMiddleware({
  target: PYTHON_BACKEND,
  changeOrigin: true,
  on: {
    proxyReq: (proxyReq, req) => {
      const expressReq = req as Request;
      proxyReq.path = expressReq.originalUrl || expressReq.url || "/";
    },
    error: (err, _req, res) => {
      logger.error({ err: err.message }, "Proxy error to Python backend");
      if (res && "writeHead" in res) {
        (res as Response).status(503).json({
          success: false,
          error:
            "Backend service is starting up. Please try again in a few seconds.",
        });
      }
    },
  },
});

const app: Express = express();

app.use(
  pinoHttp({
    logger,
    serializers: {
      req(req) {
        return {
          id: req.id,
          method: req.method,
          url: req.url?.split("?")[0],
        };
      },
      res(res) {
        return {
          statusCode: res.statusCode,
        };
      },
    },
  }),
);
app.use(cors());

const localApiPaths = ["/api/healthz"];

app.use("/api", (req, res, next) => {
  const fullPath = "/api" + req.path;
  if (localApiPaths.some((p) => fullPath.startsWith(p))) {
    return next();
  }

  if (process.env["NODE_ENV"] === "production" && !pythonReady) {
    return res.status(503).json({
      success: false,
      error:
        "Backend is starting up. Please refresh the page in about 30 seconds.",
    });
  }

  return pythonProxy(req, res, next);
});

app.use(express.json());
app.use(express.urlencoded({ extended: true }));
app.use("/api", router);

export default app;
