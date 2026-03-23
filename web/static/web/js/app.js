(function () {
  "use strict";

  const STORAGE_ACCESS = "loguea_access";
  const STORAGE_REFRESH = "loguea_refresh";
  const STORAGE_USER = "loguea_user";

  const api = (path, options = {}) => {
    return fetch(path, {
      credentials: "same-origin",
      ...options,
      headers: {
        "Content-Type": "application/json",
        ...(options.headers || {}),
      },
    });
  };

  const authHeaders = () => {
    const access = sessionStorage.getItem(STORAGE_ACCESS);
    return access ? { Authorization: "Bearer " + access } : {};
  };

  async function refreshTokens() {
    const refresh = sessionStorage.getItem(STORAGE_REFRESH);
    if (!refresh) return false;
    const res = await api("/api/auth/token/refresh/", {
      method: "POST",
      body: JSON.stringify({ refresh }),
    });
    if (!res.ok) return false;
    const data = await res.json();
    sessionStorage.setItem(STORAGE_ACCESS, data.access);
    if (data.refresh) sessionStorage.setItem(STORAGE_REFRESH, data.refresh);
    return true;
  }

  async function apiJson(path, options = {}) {
    let res = await api(path, {
      ...options,
      headers: { ...authHeaders(), ...(options.headers || {}) },
    });
    if (res.status === 401 && path.indexOf("/api/auth/") !== 0) {
      const ok = await refreshTokens();
      if (ok) {
        res = await api(path, {
          ...options,
          headers: { ...authHeaders(), ...(options.headers || {}) },
        });
      }
    }
    const text = await res.text();
    let data = null;
    try {
      data = text ? JSON.parse(text) : null;
    } catch {
      data = text;
    }
    if (!res.ok) {
      const err = new Error(
        (data && (data.detail || data.message)) || res.statusText || "Error"
      );
      err.status = res.status;
      err.body = data;
      throw err;
    }
    return data;
  }

  const el = (id) => document.getElementById(id);

  function showLoginError(msg) {
    const box = el("login-error");
    if (!msg) {
      box.hidden = true;
      box.textContent = "";
      return;
    }
    box.hidden = false;
    box.textContent = msg;
  }

  function showAppError(msg) {
    const box = el("app-error");
    if (!msg) {
      box.hidden = true;
      box.textContent = "";
      return;
    }
    box.hidden = false;
    box.textContent = msg;
  }

  function setLoggedIn(username) {
    sessionStorage.setItem(STORAGE_USER, username || "");
    el("panel-login").hidden = true;
    el("panel-app").hidden = false;
    el("top-actions").hidden = false;
    el("user-label").textContent = username || "Sesión activa";
  }

  function setLoggedOut() {
    sessionStorage.removeItem(STORAGE_ACCESS);
    sessionStorage.removeItem(STORAGE_REFRESH);
    sessionStorage.removeItem(STORAGE_USER);
    el("panel-login").hidden = false;
    el("panel-app").hidden = true;
    el("top-actions").hidden = true;
    el("tbody-products").innerHTML = "";
  }

  function isLoggedIn() {
    return !!sessionStorage.getItem(STORAGE_ACCESS);
  }

  function formatMoney(v) {
    const n = Number(v);
    if (Number.isNaN(n)) return "—";
    return n.toLocaleString("es-ES", {
      style: "currency",
      currency: "EUR",
    });
  }

  async function loadProducts() {
    showAppError("");
    const tbody = el("tbody-products");
    const empty = el("empty-products");
    tbody.innerHTML = "";
    const rows = await apiJson("/api/productos/");
    if (!Array.isArray(rows) || rows.length === 0) {
      empty.hidden = false;
      return;
    }
    empty.hidden = true;
    for (const p of rows) {
      const tr = document.createElement("tr");
      tr.innerHTML =
        "<td class=\"num\">" +
        String(p.id) +
        "</td>" +
        "<td>" +
        escapeHtml(p.nombre) +
        "</td>" +
        "<td class=\"num\">" +
        formatMoney(p.precio) +
        "</td>" +
        "<td class=\"num\">" +
        String(p.stock) +
        "</td>" +
        '<td><div class="row-actions">' +
        '<button type="button" class="btn ghost icon btn-edit" data-id="' +
        p.id +
        '">Editar</button>' +
        '<button type="button" class="btn danger btn-delete" data-id="' +
        p.id +
        '">Eliminar</button>' +
        "</div></td>";
      tbody.appendChild(tr);
    }
    tbody.querySelectorAll(".btn-edit").forEach((b) => {
      b.addEventListener("click", () => {
        openDialog(Number(b.getAttribute("data-id"))).catch((e) =>
          showAppError(e.message || "No se pudo cargar el producto.")
        );
      });
    });
    tbody.querySelectorAll(".btn-delete").forEach((b) => {
      b.addEventListener("click", () => deleteProduct(Number(b.getAttribute("data-id"))));
    });
  }

  function escapeHtml(s) {
    const d = document.createElement("div");
    d.textContent = s;
    return d.innerHTML;
  }

  const dialog = el("dialog-product");

  async function openDialog(id) {
    el("dialog-title").textContent = id ? "Editar producto" : "Nuevo producto";
    el("field-id").value = id ? String(id) : "";
    el("field-nombre").value = "";
    el("field-precio").value = "";
    el("field-stock").value = "";
    if (id) {
      const p = await apiJson("/api/productos/" + id + "/");
      el("field-nombre").value = p.nombre || "";
      el("field-precio").value = p.precio != null ? String(p.precio) : "";
      el("field-stock").value = p.stock != null ? String(p.stock) : "";
    }
    dialog.showModal();
    el("field-nombre").focus();
  }

  function closeDialog() {
    dialog.close();
  }

  async function deleteProduct(id) {
    if (!confirm("¿Eliminar este producto?")) return;
    showAppError("");
    try {
      await apiJson("/api/productos/" + id + "/", { method: "DELETE" });
      await loadProducts();
    } catch (e) {
      showAppError(e.message || "No se pudo eliminar.");
    }
  }

  el("form-login").addEventListener("submit", async (ev) => {
    ev.preventDefault();
    showLoginError("");
    const fd = new FormData(ev.target);
    const username = String(fd.get("username") || "").trim();
    const password = String(fd.get("password") || "");
    try {
      const data = await apiJson("/api/auth/login/", {
        method: "POST",
        body: JSON.stringify({ username, password }),
      });
      sessionStorage.setItem(STORAGE_ACCESS, data.access);
      sessionStorage.setItem(STORAGE_REFRESH, data.refresh);
      setLoggedIn(username);
      await loadProducts();
    } catch (e) {
      showLoginError(
        e.status === 401
          ? "Usuario o contraseña incorrectos."
          : e.message || "No se pudo iniciar sesión."
      );
    }
  });

  el("btn-logout").addEventListener("click", () => {
    setLoggedOut();
    showLoginError("");
  });

  el("btn-new").addEventListener("click", () => {
    openDialog(null).catch((e) => showAppError(e.message || "Error."));
  });
  el("btn-cancel").addEventListener("click", closeDialog);

  el("form-product").addEventListener("submit", async (ev) => {
    ev.preventDefault();
    const id = el("field-id").value;
    const payload = {
      nombre: el("field-nombre").value.trim(),
      precio: el("field-precio").value,
      stock: parseInt(el("field-stock").value, 10),
    };
    showAppError("");
    try {
      if (id) {
        await apiJson("/api/productos/" + id + "/", {
          method: "PUT",
          body: JSON.stringify(payload),
        });
      } else {
        await apiJson("/api/productos/", {
          method: "POST",
          body: JSON.stringify(payload),
        });
      }
      closeDialog();
      await loadProducts();
    } catch (e) {
      const detail = e.body && typeof e.body === "object" ? JSON.stringify(e.body) : e.message;
      showAppError(detail || "Error al guardar.");
    }
  });

  if (isLoggedIn()) {
    setLoggedIn(sessionStorage.getItem(STORAGE_USER) || "");
    loadProducts().catch((e) => {
      showAppError(e.message || "Sesión caducada.");
      setLoggedOut();
    });
  }
})();
