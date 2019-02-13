import { EditorState, RichUtils } from "draft-js";
import * as React from "react";

interface LinkSourceProps {
  editorState: EditorState;
  entityType: {
    type: string;
  };
  onComplete: (updateState: EditorState) => void;
}

class LinkSource extends React.Component<LinkSourceProps> {
  componentDidMount() {
    const { editorState, entityType, onComplete } = this.props;

    const href = window.prompt("Link URL");

    if (href) {
      const content = editorState.getCurrentContent();
      const contentWithEntity = content.createEntity(
        entityType.type,
        "MUTABLE",
        { href }
      );
      const entityKey = contentWithEntity.getLastCreatedEntityKey();
      const newEditorState = EditorState.set(editorState, {
        currentContent: contentWithEntity
      });
      const nextState = RichUtils.toggleLink(
        newEditorState,
        newEditorState.getSelection(),
        entityKey
      );

      onComplete(nextState);
    } else {
      onComplete(editorState);
    }
  }

  render() {
    return null;
  }
}
export default LinkSource;
