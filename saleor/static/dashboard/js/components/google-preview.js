const $seoTitle = $('#seo_title');

const $nameId = $seoTitle.data('bind');
const $name = $(`#${$nameId}`);

const $seoDescription = $('#seo_description');
const $descriptionMaterialize = $seoDescription.data('materialize');
if ($descriptionMaterialize) {
  var $description = $(`.materialize-textarea[name='${$descriptionMaterialize}']`);
} else {
  const $descriptionId = $seoDescription.data('bind');
  var $description = $(`#${$descriptionId}`);
}

const $googleTitlePreview = $('#google-preview-title');
const $googleDescriptionPreview = $('#google-preview-description');
const $preview = $('.preview');
const $previewErrors = $('#preview-error');

const watchedEvents = 'input propertychange cut paste copy change';

function checkForErrors() {
  const $descriptionText = $googleDescriptionPreview.text();
  const $titleText = $googleTitlePreview.text();
  if ($descriptionText && $titleText) {
    $preview.show();
    $previewErrors.hide();
  } else if (!$descriptionText && !$titleText) {
    $preview.hide();
    $previewErrors.text(gettext('Please provide title and description to see how this product might appear in search engine results.'));
    $previewErrors.show();
  } else if (!$descriptionText) {
    $preview.hide();
    $previewErrors.text(gettext('Please provide description to see how this product might appear in search engine results.'));
    $previewErrors.show();
  } else if (!$titleText) {
    $preview.hide();
    $previewErrors.text(gettext('Please provide title to see how this product might appear in search engine results.'));
    $previewErrors.show();
  }
}

function truncate(text, seoField) {
  const $fieldMaxLength = seoField.prop('maxLength');
  if ($fieldMaxLength === -1) {
    // console.log('Field maxlength is not defined');
    return text;
  }
  return text.substring(text, $fieldMaxLength);
}

function updatePlaceholderOnInput(field, seoField, previewField) {
  field.on(watchedEvents, (e) => {
    const $target = $(e.currentTarget);
    const $placeholderText = $target.val();
    seoField.attr('placeholder', truncate($placeholderText, seoField));
    const $seoText = seoField.val();
    if (!$seoText) {
      previewField.text(truncate($placeholderText, seoField));
    }
    checkForErrors();
  });
}

function updatePreviewOnInput(seoField, previewField) {
  seoField.on(watchedEvents, (e) => {
    const $target = $(e.currentTarget);
    const $currentText = $target.val();
    if ($currentText) {
      previewField.text(truncate($currentText, seoField));
    } else {
      const $placeholderValue = seoField.attr('placeholder');
      previewField.text(truncate($placeholderValue, seoField));
    }
    checkForErrors();
  });
}

checkForErrors();
updatePlaceholderOnInput($name, $seoTitle, $googleTitlePreview);
updatePlaceholderOnInput($description, $seoDescription, $googleDescriptionPreview);
updatePreviewOnInput($seoTitle, $googleTitlePreview);
updatePreviewOnInput($seoDescription, $googleDescriptionPreview);
