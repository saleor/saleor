const $seoTitle = $('#id_seo_title');
const $seoDescription = $('#id_seo_description');

$seoTitle.on('input propertychange', function (e) {
  const $target = $(e.currentTarget);
  const $currentText = $target.val();
  const $googlePreview = $('#google-preview-title');
  $googlePreview.text($currentText);
});

$seoDescription.on('input propertychange', function (e) {
  console.log('DUPA');
  const $target = $(e.currentTarget);
  const $currentText = $target.val();
  const $googlePreview = $('#google-preview-description');
  $googlePreview.text($currentText);
});
