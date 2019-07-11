import { RawDraftContentState } from "draft-js";
import draftToHtml from "draftjs-to-html";
import React from "react";

interface DraftRendererProps {
  content: RawDraftContentState;
}

const DraftRenderer: React.FC<DraftRendererProps> = ({ content }) => (
  <div
    dangerouslySetInnerHTML={{
      __html: draftToHtml(content)
    }}
  />
);
DraftRenderer.displayName = "DraftRenderer";
export default DraftRenderer;
