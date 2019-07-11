export const getContentWindowHeight = () => {
  const headerRef = document.getElementById("header");
  const footerRef = document.getElementById("footer");
  const headerHeight = headerRef ? headerRef.offsetHeight : 0;
  const footerHeight = footerRef ? footerRef.offsetHeight : 0;

  return window.innerHeight - headerHeight - footerHeight;
};
