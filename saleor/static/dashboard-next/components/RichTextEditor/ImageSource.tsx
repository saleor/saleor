import Button from "@material-ui/core/Button";
import Dialog from "@material-ui/core/Dialog";
import DialogActions from "@material-ui/core/DialogActions";
import DialogContent from "@material-ui/core/DialogContent";
import DialogTitle from "@material-ui/core/DialogTitle";
import TextField from "@material-ui/core/TextField";
import { AtomicBlockUtils, EditorState, EntityInstance } from "draft-js";
import * as React from "react";

import i18n from "../../i18n";
import Form from "../Form";

interface ImageSourceProps {
  editorState: EditorState;
  entity?: EntityInstance;
  entityKey?: string;
  entityType: {
    type: string;
  };
  onComplete: (updateState: EditorState) => void;
  onClose: () => void;
}

class ImageSource extends React.Component<ImageSourceProps> {
  submit = (href: string) => {
    const {
      editorState,
      entity,
      entityKey,
      entityType,
      onComplete
    } = this.props;

    if (href) {
      const content = editorState.getCurrentContent();
      if (entity) {
        const nextContent = content.mergeEntityData(entityKey, { href });
        const nextState = EditorState.push(
          editorState,
          nextContent,
          "apply-entity"
        );
        onComplete(nextState);
      } else {
        const contentWithEntity = content.createEntity(
          entityType.type,
          "IMMUTABLE",
          { href }
        );
        const nextState = AtomicBlockUtils.insertAtomicBlock(
          editorState,
          contentWithEntity.getLastCreatedEntityKey(),
          " "
        );

        onComplete(nextState);
      }
    } else {
      onComplete(editorState);
    }
  };

  render() {
    const { entity, onClose } = this.props;
    const initial = entity ? entity.getData().href : "";

    return (
      <Dialog open={true} fullWidth maxWidth="sm">
        <Form
          initial={{ href: initial }}
          onSubmit={({ href }) => this.submit(href)}
        >
          {({ data, change, submit }) => (
            <>
              <DialogTitle>{i18n.t("Add Image Link")}</DialogTitle>
              <DialogContent>
                <TextField
                  name="href"
                  fullWidth
                  label={i18n.t("Image URL")}
                  value={data.href}
                  onChange={change}
                />
              </DialogContent>
              <DialogActions>
                <Button onClick={onClose}>
                  {i18n.t("Cancel", { context: "button" })}
                </Button>
                <Button onClick={submit} color="primary" variant="contained">
                  {i18n.t("Save", { context: "button" })}
                </Button>
              </DialogActions>
            </>
          )}
        </Form>
      </Dialog>
    );
  }
}
export default ImageSource;
