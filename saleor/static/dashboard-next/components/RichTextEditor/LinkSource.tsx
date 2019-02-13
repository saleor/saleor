import { AtomicBlockUtils } from "draft-js";
import * as React from "react";

interface LinkSourceProps {
  editorState: any;
  entityType: {
    type: string;
  };
  onComplete: (updateState: any) => void;
}

class LinkSource extends React.Component<LinkSourceProps> {
  componentDidMount() {
    const { editorState, entityType, onComplete } = this.props;

    const src = window.prompt("Link URL");

    if (src) {
      const content = editorState.getCurrentContent();
      const contentWithEntity = content.createEntity(
        entityType.type,
        "IMMUTABLE",
        { src }
      );
      const entityKey = contentWithEntity.getLastCreatedEntityKey();
      const nextState = AtomicBlockUtils.insertAtomicBlock(
        editorState,
        entityKey,
        " "
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
