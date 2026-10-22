/**
 * Minimal progressive enhancement for CPF and Brazilian phone numbers.
 *
 * Keep backend validation authoritative. Only known operational identity fields
 * are masked; clinical/free-text, authentication and global mixed search inputs
 * are intentionally excluded. Delegated events survive Reflex route changes.
 */
(function () {
  "use strict";
  if (window.__vittaInputMasksInstalled) return;
  window.__vittaInputMasksInstalled = true;

  const MASKS = {
    "patient-search-cpf": "cpf",
    "patient-create-cpf": "cpf",
    "agenda-patient-cpf": "cpf",
    "patient-create-phone": "phone",
    "patient-edit-phone": "phone",
  };

  function digitsOnly(value, limit) {
    return String(value || "").replace(/\D/g, "").slice(0, limit);
  }

  function maskCpf(value) {
    const d = digitsOnly(value, 11);
    if (d.length <= 3) return d;
    if (d.length <= 6) return d.slice(0, 3) + "." + d.slice(3);
    if (d.length <= 9) return d.slice(0, 3) + "." + d.slice(3, 6) + "." + d.slice(6);
    return d.slice(0, 3) + "." + d.slice(3, 6) + "." + d.slice(6, 9) + "-" + d.slice(9);
  }

  function maskPhone(value) {
    const d = digitsOnly(value, 11);
    if (d.length <= 2) return d.length ? "(" + d : "";
    const area = "(" + d.slice(0, 2) + ") ";
    if (d.length <= 6) return area + d.slice(2);
    const split = d.length > 10 ? 7 : 6;
    return area + d.slice(2, split) + "-" + d.slice(split);
  }

  function validCpf(value) {
    const d = digitsOnly(value, 11);
    if (d.length !== 11 || /^(\d)\1{10}$/.test(d)) return false;
    function check(size) {
      let sum = 0;
      for (let i = 0; i < size; i++) sum += Number(d[i]) * (size + 1 - i);
      const remainder = (sum * 10) % 11;
      return (remainder === 10 ? 0 : remainder) === Number(d[size]);
    }
    return check(9) && check(10);
  }

  function refreshValidity(input, kind) {
    if (kind !== "cpf") return;
    const count = digitsOnly(input.value, 11).length;
    input.setCustomValidity(count === 11 && !validCpf(input.value)
      ? "CPF inválido. Confira os dígitos informados." : "");
  }

  function applyMask(input) {
    const kind = MASKS[input.id];
    if (!kind || !input.matches('input')) return;
    const previous = input.value;
    const formatted = kind === "cpf" ? maskCpf(previous) : maskPhone(previous);
    if (formatted !== previous) {
      // Use the native setter so React/Reflex can still observe user edits.
      const nativeSetter = Object.getOwnPropertyDescriptor(
        HTMLInputElement.prototype, "value"
      ).set;
      nativeSetter.call(input, formatted);
      if (input === document.activeElement && input.selectionStart != null) {
        input.setSelectionRange(formatted.length, formatted.length);
      }
    }
    refreshValidity(input, kind);
  }

  document.addEventListener("input", (event) => {
    if (event.target instanceof HTMLInputElement && MASKS[event.target.id]) {
      applyMask(event.target);
    }
  }, true);

  document.addEventListener("focusin", (event) => {
    if (event.target instanceof HTMLInputElement && MASKS[event.target.id]) {
      applyMask(event.target);
    }
  }, true);
})();
