import assert from "node:assert/strict";
import { test } from "node:test";

import { checkUrl } from "../src/checker.js";

test("returns up for a 200 response", async () => {
  const fakeFetch = async () => ({ ok: true, status: 200 });

  const outcome = await checkUrl("https://example.com", { fetchImpl: fakeFetch });

  assert.equal(outcome.result, "up");
  assert.equal(outcome.httpStatus, 200);
  assert.equal(outcome.error, "");
});

test("returns down for a 500 response", async () => {
  const fakeFetch = async () => ({ ok: false, status: 500 });

  const outcome = await checkUrl("https://example.com", { fetchImpl: fakeFetch });

  assert.equal(outcome.result, "down");
  assert.equal(outcome.httpStatus, 500);
});

test("returns down with the error message on network failure", async () => {
  const fakeFetch = async () => {
    throw new Error("getaddrinfo ENOTFOUND");
  };

  const outcome = await checkUrl("https://nope.invalid", { fetchImpl: fakeFetch });

  assert.equal(outcome.result, "down");
  assert.equal(outcome.httpStatus, 0);
  assert.match(outcome.error, /ENOTFOUND/);
});

test("reports a timeout", async () => {
  const fakeFetch = async () => {
    const err = new Error("The operation was aborted");
    err.name = "TimeoutError";
    throw err;
  };

  const outcome = await checkUrl("https://slow.example.com", { fetchImpl: fakeFetch });

  assert.equal(outcome.result, "down");
  assert.equal(outcome.error, "timeout");
});
