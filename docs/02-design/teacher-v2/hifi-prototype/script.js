const navItems = document.querySelectorAll(".top-nav__item");
const screens = document.querySelectorAll(".screen");

navItems.forEach((item) => {
  item.addEventListener("click", () => {
    const target = item.dataset.screen;

    navItems.forEach((nav) => nav.classList.remove("is-active"));
    item.classList.add("is-active");

    screens.forEach((screen) => {
      screen.classList.toggle("is-active", screen.id === target);
    });

    window.scrollTo({ top: 0, behavior: "smooth" });
  });
});
