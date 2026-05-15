"use client";

import { createContext, useContext, useState, useEffect } from "react";
import { api } from "@/lib/api";
import { supabase } from "@/lib/supabase";

type User = {
  name: string;
  role: "user";       // only one role now — doctor removed
  avatar: string;
};

type UserCtx = {
  user: User;
  setUser: (u: User) => void;
  logout: () => void;
};

const defaultUser: User = { name: "User", role: "user", avatar: "U" };

const UserContext = createContext<UserCtx>({
  user: defaultUser,
  setUser: () => {},
  logout: () => {},
});

export function UserProvider({ children }: { children: React.ReactNode }) {
  const [user, setUserState] = useState<User>(defaultUser);

  useEffect(() => {
    const token = localStorage.getItem("nn_token");
    if (token) {
      api.me()
        .then(me => {
          const restored: User = {
            name:   me.name,
            role:   "user",
            avatar: me.name.charAt(0).toUpperCase(),
          };
          setUserState(restored);
          localStorage.setItem("nn_user", JSON.stringify(restored));
        })
        .catch(() => {
          const stored = localStorage.getItem("nn_user");
          if (stored) {
            try { setUserState(JSON.parse(stored)); } catch {}
          }
        });
    } else {
      const stored = localStorage.getItem("nn_user");
      if (stored) {
        try { setUserState(JSON.parse(stored)); } catch {}
      }
    }
  }, []);

  function setUser(u: User) {
    setUserState(u);
    localStorage.setItem("nn_user", JSON.stringify(u));
  }

  async function logout() {
    await supabase.auth.signOut();
    localStorage.removeItem("nn_token");
    localStorage.removeItem("nn_user");
    setUserState(defaultUser);
  }

  return (
    <UserContext.Provider value={{ user, setUser, logout }}>
      {children}
    </UserContext.Provider>
  );
}

export function useUser() {
  return useContext(UserContext);
}
