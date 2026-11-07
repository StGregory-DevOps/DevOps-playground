/**
 * Check one URL. Never throws: network errors and timeouts become a "down" result.
 * fetchImpl can be replaced in tests.
 */
export async function checkUrl(url, { timeoutMs = 5000, fetchImpl = fetch } = {}) {
  const started = Date.now();
  try {
    const response = await fetchImpl(url, {
      method: "GET",
      redirect: "follow",
      signal: AbortSignal.timeout(timeoutMs),
    });
    return {
      result: response.ok ? "up" : "down",
      httpStatus: response.status,
      responseMs: Date.now() - started,
      error: "",
    };
  } catch (err) {
    return {
      result: "down",
      httpStatus: 0,
      responseMs: Date.now() - started,
      error: err.name === "TimeoutError" ? "timeout" : err.message,
    };
  }
}
