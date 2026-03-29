import app from "./app";
import { logger } from "./lib/logger";
import { spawn, execSync, type ChildProcess } from "child_process";
import path from "path";
import { fileURLToPath } from "url";

const rawPort = process.env["PORT"];

if (!rawPort) {
  throw new Error(
    "PORT environment variable is required but was not provided.",
  );
}

const port = Number(rawPort);

if (Number.isNaN(port) || port <= 0) {
  throw new Error(`Invalid PORT value: "${rawPort}"`);
}

let pythonProcess: ChildProcess | null = null;
const isProduction = process.env["NODE_ENV"] === "production";

function findPython(): string {
  for (const cmd of ["python3", "python"]) {
    try {
      execSync(`which ${cmd}`, { stdio: "pipe" });
      return cmd;
    } catch {}
  }
  return "python3";
}

function startPythonBackend() {
  const workspaceRoot = path.resolve(
    path.dirname(fileURLToPath(import.meta.url)),
    "..",
    "..",
    "..",
  );
  const backendDir = path.join(workspaceRoot, "backend");
  const pythonCmd = findPython();

  logger.info({ backendDir, pythonCmd }, "Starting Python backend");

  try {
    const pythonVersion = execSync(`${pythonCmd} --version`, {
      encoding: "utf-8",
    }).trim();
    logger.info({ pythonVersion }, "Python version detected");
  } catch (e) {
    logger.error("Python not found, backend will not start");
    return;
  }

  try {
    logger.info("Installing Python dependencies...");
    execSync(`${pythonCmd} -m pip install -r requirements.txt --quiet --disable-pip-version-check`, {
      cwd: backendDir,
      stdio: "pipe",
      timeout: 120000,
    });
    logger.info("Python dependencies installed");
  } catch (e) {
    logger.warn("pip install may have had issues, continuing anyway");
  }

  pythonProcess = spawn(
    pythonCmd,
    [
      "-m",
      "uvicorn",
      "app.main:app",
      "--host",
      "0.0.0.0",
      "--port",
      "8000",
    ],
    {
      cwd: backendDir,
      stdio: "pipe",
      env: { ...process.env, PYTHONUNBUFFERED: "1" },
    },
  );

  pythonProcess.stdout?.on("data", (data: Buffer) => {
    const lines = data.toString().trim().split("\n");
    for (const line of lines) {
      logger.info({ source: "python" }, line);
    }
  });

  pythonProcess.stderr?.on("data", (data: Buffer) => {
    const lines = data.toString().trim().split("\n");
    for (const line of lines) {
      if (line.includes("ERROR") || line.includes("Traceback")) {
        logger.error({ source: "python" }, line);
      } else {
        logger.info({ source: "python-stderr" }, line);
      }
    }
  });

  pythonProcess.on("error", (err) => {
    logger.error({ err: err.message }, "Failed to spawn Python backend");
  });

  pythonProcess.on("exit", (code, signal) => {
    logger.warn({ code, signal }, "Python backend exited");
    if (isProduction && code !== 0) {
      logger.info("Restarting Python backend in 5 seconds...");
      setTimeout(startPythonBackend, 5000);
    }
  });
}

if (isProduction) {
  startPythonBackend();
}

function shutdown() {
  logger.info("Shutting down...");
  if (pythonProcess && !pythonProcess.killed) {
    pythonProcess.kill("SIGTERM");
  }
  process.exit(0);
}

process.on("SIGTERM", shutdown);
process.on("SIGINT", shutdown);

app.listen(port, (err) => {
  if (err) {
    logger.error({ err }, "Error listening on port");
    process.exit(1);
  }

  logger.info({ port }, "Server listening");
});
