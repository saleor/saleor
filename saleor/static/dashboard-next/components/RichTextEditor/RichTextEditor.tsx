import {
  createStyles,
  Theme,
  withStyles,
  WithStyles
} from "@material-ui/core/styles";
import {
  BLOCK_TYPE,
  DraftailEditor,
  ENTITY_TYPE,
  INLINE_STYLE
} from "draftail";
import * as React from "react";
import Link from "./Link";
import LinkSource from "./LinkSource";

export interface RichTextEditorProps {
  disabled: boolean;
  name: string;
  initial: string;
  onChange: (event: React.ChangeEvent<any>) => void;
}

const styles = (theme: Theme) =>
  createStyles({
    root: {
      "& .Draftail-Toolbar": {
        display: "flex"
      }
    }
  });
const RichTextEditor = withStyles(styles, { name: "RichTextEditor" })(
  ({
    classes,
    initial,
    name,
    onChange
  }: RichTextEditorProps & WithStyles<typeof styles>) => (
    <div className={classes.root}>
      <DraftailEditor
        rawContentState={initial || null}
        onSave={value =>
          onChange({
            target: {
              name,
              value
            }
          } as any)
        }
        blockTypes={[
          { type: BLOCK_TYPE.HEADER_TWO },
          { type: BLOCK_TYPE.HEADER_THREE },
          { type: BLOCK_TYPE.BLOCKQUOTE },
          { type: BLOCK_TYPE.UNORDERED_LIST_ITEM },
          { type: BLOCK_TYPE.ORDERED_LIST_ITEM }
        ]}
        inlineStyles={[
          { type: INLINE_STYLE.BOLD },
          { type: INLINE_STYLE.ITALIC }
        ]}
        entityTypes={[
          {
            attributes: ["url"],
            decorator: Link,
            source: LinkSource,
            type: ENTITY_TYPE.LINK
          },
          { type: ENTITY_TYPE.HORIZONTAL_RULE }
        ]}
      />
    </div>
  )
);
RichTextEditor.displayName = "RichTextEditor";
export default RichTextEditor;
