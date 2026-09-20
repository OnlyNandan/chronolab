// Cognito login + token storage for ChronoLab (MIGRATION_PLAN.md Phase 3).
//
// Calls Cognito's InitiateAuth directly over its public JSON API — no AWS SDK
// needed, since USER_PASSWORD_AUTH only requires the app client ID (public,
// not a secret) and doesn't need SigV4 signing.

const COGNITO_REGION = import.meta.env.VITE_AWS_REGION;
const COGNITO_CLIENT_ID = import.meta.env.VITE_COGNITO_APP_CLIENT_ID;

const STORAGE_KEY = 'chronolab_session';

function decodeJwtPayload(token) {
  const payload = token.split('.')[1];
  const json = atob(payload.replace(/-/g, '+').replace(/_/g, '/'));
  return JSON.parse(json);
}

export async function login(username, password) {
  if (!COGNITO_REGION || !COGNITO_CLIENT_ID) {
    throw new Error('Cognito is not configured (VITE_AWS_REGION / VITE_COGNITO_APP_CLIENT_ID missing). Run scripts/bootstrap.sh first.');
  }

  const res = await fetch(`https://cognito-idp.${COGNITO_REGION}.amazonaws.com/`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/x-amz-json-1.1',
      'X-Amz-Target': 'AWSCognitoIdentityProviderService.InitiateAuth',
    },
    body: JSON.stringify({
      AuthFlow: 'USER_PASSWORD_AUTH',
      ClientId: COGNITO_CLIENT_ID,
      AuthParameters: { USERNAME: username, PASSWORD: password },
    }),
  });

  const data = await res.json();
  if (!res.ok) {
    throw new Error(data.message || data.__type || 'Login failed');
  }

  const idToken = data.AuthenticationResult.IdToken;
  const claims = decodeJwtPayload(idToken);
  const session = {
    idToken,
    accessToken: data.AuthenticationResult.AccessToken,
    role: claims['custom:role'] || null,
    patientId: claims['custom:patient_id'] || null,
    username: claims['cognito:username'] || claims['email'] || username,
  };
  localStorage.setItem(STORAGE_KEY, JSON.stringify(session));
  return session;
}

export function getSession() {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    return raw ? JSON.parse(raw) : null;
  } catch {
    return null;
  }
}

export function logout() {
  localStorage.removeItem(STORAGE_KEY);
}

export function authFetch(url, options = {}) {
  const session = getSession();
  const headers = { ...(options.headers || {}) };
  if (session?.idToken) {
    headers['Authorization'] = `Bearer ${session.idToken}`;
  }
  return fetch(url, { ...options, headers });
}

// Browsers can't set headers on the WebSocket handshake, so the token travels
// as a query param instead — the backend reads it from there (see server.py).
export function authWsUrl(baseWsUrl) {
  const session = getSession();
  if (!session?.idToken) return baseWsUrl;
  const separator = baseWsUrl.includes('?') ? '&' : '?';
  return `${baseWsUrl}${separator}token=${encodeURIComponent(session.idToken)}`;
}
