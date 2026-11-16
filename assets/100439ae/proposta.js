/* proposta.js — interazioni minime della pagina di proposta.
   Nessuna dipendenza esterna. Rispetta prefers-reduced-motion. */

(function () {
  "use strict";

  var barra = document.querySelector(".scelta-fissa");
  var sezioneOpzioni = document.getElementById("opzioni");

  /* --- barra di scelta fissa: compare quando le opzioni sono passate del tutto --- */
  if (barra && sezioneOpzioni) {
    var inProgramma = false;
    var aggiornaBarra = function () {
      inProgramma = false;
      var rect = sezioneOpzioni.getBoundingClientRect();
      // la sezione opzioni e' completamente uscita dal basso? no: e' passata in alto
      barra.classList.toggle("visibile", rect.bottom < 0);
    };
    var richiedi = function () {
      if (inProgramma) return;
      inProgramma = true;
      window.requestAnimationFrame(aggiornaBarra);
    };
    window.addEventListener("scroll", richiedi, { passive: true });
    window.addEventListener("resize", richiedi, { passive: true });
    aggiornaBarra();
  }

  /* --- copia link --- */
  document.querySelectorAll("[data-copia-link]").forEach(function (el) {
    el.addEventListener("click", function (event) {
      event.preventDefault();
      var testo = el.getAttribute("data-copia-link") || window.location.href;
      var fatto = function () {
        var originale = el.textContent;
        el.textContent = "Link copiato";
        window.setTimeout(function () { el.textContent = originale; }, 1800);
      };
      if (navigator.clipboard && navigator.clipboard.writeText) {
        navigator.clipboard.writeText(testo).then(fatto).catch(function () {});
      }
    });
  });

  /* --- stampa --- */
  document.querySelectorAll("[data-stampa]").forEach(function (el) {
    el.addEventListener("click", function (event) {
      event.preventDefault();
      window.print();
    });
  });

  /* --- rivelazione morbida delle sezioni --- */
  var ridotto = window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  if (!ridotto && "IntersectionObserver" in window) {
    var sezioni = document.querySelectorAll(".reveal");
    sezioni.forEach(function (el) { el.classList.add("reveal--attivo"); });
  }
})();
