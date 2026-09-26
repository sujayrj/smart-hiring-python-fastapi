import { createContext, useContext, useEffect, useState } from "react";
import { api, clearToken, getToken, setToken } from "../services/api";

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!getToken()) {
      setLoading(false);
      return;
    }
    api
      .me()
      .then(setUser)
      .catch(() => clearToken())
      .finally(() => setLoading(false));
  }, []);

  async function login(username, password) {
    const res = await api.login(username, password);
    setToken(res.access_token);
    const me = await api.me();
    setUser(me);
    return me;
  }

  function logout() {
    clearToken();
    setUser(null);
  }

  return (
    <AuthContext.Provider value={{ user, loading, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export const useAuth = () => useContext(AuthContext);

export const homeFor = (role) =>
  role === "ADMIN" ? "/admin" : role === "INTERVIEWER" ? "/interviewer" : "/candidate";
