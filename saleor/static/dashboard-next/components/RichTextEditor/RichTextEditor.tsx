import {
  createStyles,
  Theme,
  withStyles,
  WithStyles
} from "@material-ui/core/styles";
import { fade } from "@material-ui/core/styles/colorManipulator";
import Typography from "@material-ui/core/Typography";
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
  label: string;
  name: string;
  initial: string;
  onChange: (event: React.ChangeEvent<any>) => void;
}

const styles = (theme: Theme) =>
  createStyles({
    label: {
      marginBottom: theme.spacing.unit * 2
    },
    root: {
      "& .DraftEditor": {
        "&-editorContainer": {
          "&:after": {
            background: theme.palette.primary.main,
            bottom: -1,
            content: "''",
            display: "block",
            height: 2,
            position: "absolute",
            transform: "scaleX(0)",
            transition: theme.transitions.duration.short + "ms",
            width: "100%"
          },
          "&:hover": {
            borderBottom: ``
          },
          borderBottom: `1px ${theme.palette.grey[500]} solid`,
          paddingBottom: theme.spacing.unit / 2,
          position: "relative"
        },
        "&-root": {
          ...theme.typography.body1
        }
      },
      "& .Draftail": {
        "&-Editor": {
          "&--focus": {
            "& .DraftEditor": {
              "&-editorContainer": {
                "&:after": {
                  transform: "scaleX(1)"
                }
              }
            }
          }
        },
        "&-Toolbar": {
          "&Button": {
            "&--active": {
              "&:hover": {
                background: fade(theme.palette.secondary.main, 0.4)
              },

              background: fade(theme.palette.secondary.main, 0.3)
            },
            "&:hover": {
              background: fade(theme.palette.secondary.main, 0.1)
            },
            alignItems: "center",
            background: "none",
            border: "none",
            borderRadius: 4,
            cursor: "pointer",
            display: "inline-flex",
            height: 24,
            justifyContent: "center",
            marginLeft: theme.spacing.unit,
            marginRight: theme.spacing.unit,
            padding: 0,
            transition: theme.transitions.duration.short + "ms",
            width: 24
          },
          "&Group": {
            display: "flex"
          },
          border: `1px ${theme.palette.grey[300]} solid`,
          borderRadius: 6,
          display: "flex",
          marginBottom: theme.spacing.unit,
          paddingBottom: theme.spacing.unit,
          paddingTop: theme.spacing.unit
        }
      }
    }
  });
const RichTextEditor = withStyles(styles, { name: "RichTextEditor" })(
  ({
    classes,
    initial,
    label,
    name,
    onChange
  }: RichTextEditorProps & WithStyles<typeof styles>) => (
    <div className={classes.root}>
      <Typography className={classes.label} variant="caption" color="primary">
        {label}
      </Typography>
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
