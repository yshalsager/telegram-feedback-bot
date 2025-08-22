import { session } from "$lib/stores.svelte.js";
import { get } from "svelte/store";

/**
 * Get the CSRF token
 * @returns {Promise<string>} - The CSRF token
 */
export async function csrf_token() {
  const response = await fetch("/api/csrf/");
  const data = await response.json();
  return data.csrf_token;
}

/**
 * Validate the user session
 * @param {string} rawInitData - The raw init data from the Telegram WebApp
 * @returns {Promise<boolean>} - True if the user is valid, false otherwise
 */
export async function validate_user(rawInitData) {
  const response = await fetch("/api/validate_user/", {
    method: "POST",
    body: JSON.stringify({ initData: rawInitData }),
    headers: {
      "Content-Type": "application/json",
      "X-CSRFToken": get(session).csrfToken || "",
    },
  });
  const data = await response.json();
  return Boolean(data.status === "success" && data.user);
}
