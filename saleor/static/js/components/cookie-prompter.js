export default $(document).ready(() => {
  const cookieName = 'cookieLaw';
  const cookieValue = '1';
  const cookieContainer = document.getElementById('cookie-prompter');

  // - get saved cookie and check if it has the expected value
  //   if the cookie has the expected value, we don't prompt to accept cookies.
  //
  // - if the cookie is not set and there is no cookie prompter container,
  //   do nothing, don't try to show the box as it doesn't exist.
  //
  if ($.cookie(cookieName) === cookieValue || !cookieContainer) {
    return;
  }

  // get the 'I accept' button
  const cookieBtn = cookieContainer.getElementsByTagName('button')[0];

  // set the prompter box to be visible as we didn't find the cookie
  cookieContainer.style.display = 'block';

  // listen for a click on the 'I accept' button
  cookieBtn.addEventListener('click', function () {
    // create a cookie to remember the 'I accept' click for 90 days
    $.cookie(cookieName, cookieValue, {expires: 90});
    cookieContainer.style.display = 'none';
  });
});
