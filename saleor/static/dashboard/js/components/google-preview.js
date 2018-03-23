const $seoTitle = $('#seo_title');

const $nameId = $seoTitle.data('bind');
const $name = $(`#${$nameId}`);

const $seoDescription = $('#seo_description');
const $descriptionMaterialize = $seoDescription.data('materialize');
let $description = '';
if ($descriptionMaterialize) {
  $description = $(`.materialize-textarea[name='${$descriptionMaterialize}']`);
} else {
  const $descriptionId = $seoDescription.data('bind');
  if ($descriptionId) {
    $description = $(`#${$descriptionId}`);
  }
}

const $googleTitlePreview = $('#google-preview-title');
const $googleDescriptionPreview = $('#google-preview-description');
const $preview = $('#google-preview');
const $previewErrors = $('#preview-error');

const watchedEvents = 'input propertychange cut paste copy change';

function updateCharsCount(field) {
  const $fieldId = field.attr('id');
  const $charCount = $(`span[data-bind=${$fieldId}]`);
  const $fieldLength = field.val().length || field.attr('placeholder').length;
  const $minRecommendedLength = field.attr('min-recommended-length');
  const $charCountWrapper = $charCount.parent();
  if ($fieldLength < $minRecommendedLength) {
    $charCountWrapper.addClass('red-text');
    $charCountWrapper.removeClass('green-text');
  } else if ($charCountWrapper.hasClass('red-text')) {
    $charCountWrapper.removeClass('red-text');
    $charCountWrapper.addClass('green-text');
  }
  $charCount.text($fieldLength);
}

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
    updateCharsCount(seoField);
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
    updateCharsCount(seoField);
  });
}

checkForErrors();
updatePlaceholderOnInput($name, $seoTitle, $googleTitlePreview);
if ($description) {
  updatePlaceholderOnInput($description, $seoDescription, $googleDescriptionPreview);
}
updatePreviewOnInput($seoTitle, $googleTitlePreview);
updatePreviewOnInput($seoDescription, $googleDescriptionPreview);
updateCharsCount($seoTitle);
updateCharsCount($seoDescription);
