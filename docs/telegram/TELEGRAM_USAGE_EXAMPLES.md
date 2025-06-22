# Telegram WebApp Integration Usage Examples

## Frontend Integration Example

### 1. React Component Example

```jsx
import React, { useEffect, useState } from "react";

function TelegramLogin() {
  const [user, setUser] = useState(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    // Check if running inside Telegram WebApp
    if (!window.Telegram || !window.Telegram.WebApp) {
      setError("Telegram WebApp not available");
      return;
    }
    // Get initDataRaw from Telegram WebApp
    const initDataRaw = window.Telegram.WebApp.initData;
    if (!initDataRaw) {
      setError("initDataRaw not found");
      return;
    }
    setLoading(true);
    // Call backend GraphQL mutation
    fetch("/graphql/", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        query: `
          mutation TelegramTokenCreate($initDataRaw: String!) {
            telegramTokenCreate(initDataRaw: $initDataRaw) {
              token
              user { email firstName lastName }
              errors { field message code }
            }
          }
        `,
        variables: { initDataRaw },
      }),
    })
      .then((res) => res.json())
      .then((result) => {
        if (result.data.telegramTokenCreate.errors.length) {
          setError(result.data.telegramTokenCreate.errors[0].message);
        } else {
          setUser(result.data.telegramTokenCreate.user);
          localStorage.setItem("token", result.data.telegramTokenCreate.token); // Store token
          window.Telegram.WebApp.sendData("login_success"); // Notify Telegram WebApp login success
        }
      })
      .catch((err) => setError("Login failed: " + err.message))
      .finally(() => setLoading(false));
  }, []);

  // Check if in Telegram WebApp environment
  if (!window.Telegram || !window.Telegram.WebApp) {
    return <div className="error">Please open this page in Telegram</div>;
  }

  // Set WebApp theme
  useEffect(() => {
    if (window.Telegram && window.Telegram.WebApp) {
      window.Telegram.WebApp.setHeaderColor("#0088cc");
    }
  }, []);

  if (error) return <div className="error">{error}</div>;
  if (user)
    return (
      <div>
        <h3>Welcome, {user.firstName}!</h3>
        <p>Email: {user.email}</p>
        <button
          onClick={() => {
            setUser(null);
            localStorage.removeItem("token");
          }}
        >
          Logout
        </button>
      </div>
    );
  return (
    <button disabled={loading} onClick={() => {}}>
      {loading ? "Logging in..." : "Login with Telegram"}
    </button>
  );
}
```

### 2. Vue.js Component Example

```vue
<template>
  <div>
    <h2>Telegram Login</h2>
    <div v-if="!isTelegramWebApp" class="error">
      Please open this page in Telegram
    </div>
    <div v-else-if="user">
      <h3>Welcome, {{ user.firstName }}!</h3>
      <p>Email: {{ user.email }}</p>
      <button @click="logout">Logout</button>
    </div>
    <button v-else :disabled="loading" @click="login">
      {{ loading ? "Logging in..." : "Login with Telegram" }}
    </button>
    <div v-if="error" class="error">{{ error }}</div>
  </div>
</template>

<script>
export default {
  data() {
    return {
      user: null,
      error: "",
      loading: false,
      isTelegramWebApp: false,
    };
  },
  mounted() {
    // Check if in Telegram WebApp environment
    this.isTelegramWebApp = !!(window.Telegram && window.Telegram.WebApp);
    if (!this.isTelegramWebApp) {
      this.error = "Telegram WebApp not available";
      return;
    }
    // Set WebApp theme
    window.Telegram.WebApp.setHeaderColor("#0088cc");
  },
  methods: {
    login() {
      this.loading = true;
      const initDataRaw = window.Telegram.WebApp.initData;
      if (!initDataRaw) {
        this.error = "initDataRaw not found";
        this.loading = false;
        return;
      }
      fetch("/graphql/", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          query: `
            mutation TelegramTokenCreate($initDataRaw: String!) {
              telegramTokenCreate(initDataRaw: $initDataRaw) {
                token
                user { email firstName lastName }
                errors { field message code }
              }
            }
          `,
          variables: { initDataRaw },
        }),
      })
        .then((res) => res.json())
        .then((result) => {
          if (result.data.telegramTokenCreate.errors.length) {
            this.error = result.data.telegramTokenCreate.errors[0].message;
          } else {
            this.user = result.data.telegramTokenCreate.user;
            localStorage.setItem(
              "token",
              result.data.telegramTokenCreate.token
            ); // Store token
            window.Telegram.WebApp.sendData("login_success"); // Notify Telegram WebApp login success
          }
        })
        .catch((err) => {
          this.error = "Login failed: " + err.message;
        })
        .finally(() => {
          this.loading = false;
        });
    },
    logout() {
      this.user = null;
      localStorage.removeItem("token");
    },
  },
};
</script>
```

## API Call Example

### 1. Using fetch

```javascript
const telegramLogin = async (initDataRaw) => {
  const response = await fetch("/graphql/", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      query: `
        mutation TelegramTokenCreate($initDataRaw: String!) {
          telegramTokenCreate(initDataRaw: $initDataRaw) {
            token
            refreshToken
            csrfToken
            user {
              id
              email
              firstName
              lastName
            }
            errors {
              field
              message
              code
            }
          }
        }
      `,
      variables: { initDataRaw },
    }),
  });

  return response.json();
};
```

### 2. Using axios

```javascript
import axios from "axios";

const telegramLogin = async (initDataRaw) => {
  const response = await axios.post("/graphql/", {
    query: `
      mutation TelegramTokenCreate($initDataRaw: String!) {
        telegramTokenCreate(initDataRaw: $initDataRaw) {
          token
          refreshToken
          csrfToken
          user {
            id
            email
            firstName
            lastName
          }
          errors {
            field
            message
            code
          }
        }
      }
    `,
    variables: { initDataRaw },
  });

  return response.data;
};
```

### 3. Using Apollo Client

```javascript
import { gql, useMutation } from "@apollo/client";

const TELEGRAM_LOGIN_MUTATION = gql`
  mutation TelegramTokenCreate($initDataRaw: String!) {
    telegramTokenCreate(initDataRaw: $initDataRaw) {
      token
      refreshToken
      csrfToken
      user {
        id
        email
        firstName
        lastName
      }
      errors {
        field
        message
        code
      }
    }
  }
`;

const useTelegramLogin = () => {
  const [login, { loading, error }] = useMutation(TELEGRAM_LOGIN_MUTATION);

  const handleLogin = async (initDataRaw) => {
    try {
      const { data } = await login({
        variables: { initDataRaw },
      });

      if (data?.telegramTokenCreate?.token) {
        // Store token
        localStorage.setItem("authToken", data.telegramTokenCreate.token);
        localStorage.setItem(
          "refreshToken",
          data.telegramTokenCreate.refreshToken
        );
        localStorage.setItem("csrfToken", data.telegramTokenCreate.csrfToken);

        return data.telegramTokenCreate;
      }
    } catch (err) {
      console.error("Login failed:", err);
      throw err;
    }
  };

  return { handleLogin, loading, error };
};
```

## Error Handling Example

```javascript
const handleTelegramLogin = async () => {
  try {
    const result = await telegramLogin(window.Telegram.WebApp.initDataRaw);
    const data = result.data?.telegramTokenCreate;

    if (data?.errors?.length > 0) {
      const error = data.errors[0];

      switch (error.code) {
        case "INVALID":
          console.error("Data validation failed:", error.message);
          break;
        case "REQUIRED":
          console.error("Missing required parameter:", error.message);
          break;
        default:
          console.error("Unknown error:", error.message);
      }

      return;
    }

    // Login success processing
    console.log("Login successful:", data.user);
  } catch (error) {
    console.error("Network error:", error);
  }
};
```

## Style Example

```css
.telegram-login {
  max-width: 400px;
  margin: 0 auto;
  padding: 20px;
  text-align: center;
}

.telegram-button {
  background: #0088cc;
  color: white;
  border: none;
  padding: 12px 24px;
  border-radius: 8px;
  font-size: 16px;
  cursor: pointer;
  transition: background-color 0.3s;
}

.telegram-button:hover {
  background: #006699;
}

.telegram-button:disabled {
  background: #cccccc;
  cursor: not-allowed;
}

.error {
  color: #ff4444;
  margin-top: 10px;
  padding: 10px;
  background: #ffeeee;
  border-radius: 4px;
}

.user-info {
  margin-top: 20px;
  padding: 20px;
  background: #f5f5f5;
  border-radius: 8px;
}

.user-info h3 {
  margin: 0 0 10px 0;
  color: #333;
}

.user-info button {
  background: #ff4444;
  color: white;
  border: none;
  padding: 8px 16px;
  border-radius: 4px;
  cursor: pointer;
  margin-top: 10px;
}

.user-info button:hover {
  background: #cc3333;
}
```

These examples show how to integrate Telegram WebApp login functionality in different frameworks and environments. Choose the implementation method that best fits your specific requirements.
