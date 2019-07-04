
import draftToHtml from 'draftjs-to-html';

export default $(document).ready((e) => {
  const data = 'data-description-json';
  const description = document.querySelector(`[${data}]`);
  if (description) {
    const parsed = JSON.parse(description.getAttribute(data));
    const content = draftToHtml(parsed);
    description.innerHTML = content;
  }
});

