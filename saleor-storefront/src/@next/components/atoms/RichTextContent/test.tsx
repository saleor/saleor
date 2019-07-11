import { shallow } from "enzyme";
import React from "react";

import { RichTextContent } from ".";
import headers from "./fixtures/headers";
import list from "./fixtures/list";
import customDescriptionJson from "./fixtures/text_blocks";
import { IProps } from "./types";

describe("<RichTextContent />", () => {
  const PROPS = {
    descriptionJson: customDescriptionJson,
  };
  const renderRichTextContent = (props: IProps) =>
    shallow(<RichTextContent {...props} />);

  it("exists", () => {
    const richTextContent = renderRichTextContent(PROPS);

    expect(richTextContent.exists()).toEqual(true);
  });

  it("should render <h1>, <h2>, <h3>", () => {
    const richTextContentHTML = renderRichTextContent({
      descriptionJson: headers,
    }).html();

    expect(richTextContentHTML.replace(/\s/g, "")).toContain(
      "<h1>h1</h1><h2>h2</h2><h3>h3</h3>"
    );
  });

  it("should render <ul>, <ol>", () => {
    const richTextContentHTML = renderRichTextContent({
      descriptionJson: list,
    }).html();

    expect(richTextContentHTML.replace(/\s/g, "")).toContain(
      "<ul><li>ul</li></ul><ol><li>ol</li></ol>"
    );
  });
});
