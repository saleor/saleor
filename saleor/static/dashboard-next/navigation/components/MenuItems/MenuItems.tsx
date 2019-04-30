import Card from "@material-ui/core/Card";
import Paper from "@material-ui/core/Paper";
import {
  createStyles,
  Theme,
  withStyles,
  WithStyles
} from "@material-ui/core/styles";
import Typography from "@material-ui/core/Typography";
import * as React from "react";
import SortableTree, { NodeRendererProps } from "react-sortable-tree";

import CardTitle from "../../../components/CardTitle";
import i18n from "../../../i18n";
import Draggable from "../../../icons/Draggable";
import { MenuDetails_menu_items } from "../../types/MenuDetails";
import {
  getDiff,
  getNodeData,
  getNodeQuantity,
  TreeNode,
  TreePermutation
} from "./tree";

const NODE_HEIGHT = 56;
const NODE_MARGIN = 40;

export interface MenuItemsProps {
  items: MenuDetails_menu_items[];
  onChange: (operation: TreePermutation) => void;
}

const styles = (theme: Theme) =>
  createStyles({
    dragIcon: {
      cursor: "grab"
    },
    nodeTitle: {
      marginLeft: theme.spacing.unit * 7
    },
    root: {
      "& .rst__collapseButton": {
        display: "none"
      },
      background: theme.palette.grey[200]
    },
    row: {
      alignItems: "center",
      background: theme.palette.background.paper,
      borderBottom: `1px ${theme.overrides.MuiCard.root.borderColor} solid`,
      borderRadius: 0,
      display: "flex",
      flexDirection: "row",
      height: NODE_HEIGHT,
      justifyContent: "flex-start",
      paddingLeft: theme.spacing.unit * 3,
      transition: theme.transitions.duration.standard + "ms"
    }
  });

const Node: React.FC<NodeRendererProps & WithStyles<typeof styles>> = ({
  classes,
  node,
  path,
  connectDragPreview,
  connectDragSource
}) => {
  return (
    <>
      {connectDragPreview(
        <div>
          <Paper
            className={classes.row}
            elevation={0}
            style={{
              marginLeft: NODE_MARGIN * (path.length - 1)
            }}
          >
            {connectDragSource(
              <div>
                <Draggable className={classes.dragIcon} />
              </div>
            )}
            <Typography className={classes.nodeTitle}>{node.title}</Typography>
          </Paper>
        </div>
      )}
    </>
  );
};

const MenuItems = withStyles(styles, { name: "MenuItems" })(
  ({
    classes,
    items,
    onChange
  }: MenuItemsProps & WithStyles<typeof styles>) => (
    <Card>
      <CardTitle title={i18n.t("Menu Items")} />
      <div style={{ height: getNodeQuantity(items) * NODE_HEIGHT }}>
        <SortableTree
          className={classes.root}
          generateNodeProps={({ path }) => ({
            className: classes.row,
            style: {
              marginLeft: NODE_MARGIN * (path.length - 1)
            }
          })}
          isVirtualized={false}
          rowHeight={NODE_HEIGHT}
          treeData={items.map(getNodeData)}
          theme={{
            nodeContentRenderer: (props => (
              <Node {...props} classes={classes} />
            )) as any
          }}
          onChange={newTree =>
            onChange(getDiff(items.map(getNodeData), newTree as TreeNode[]))
          }
        />
      </div>
    </Card>
  )
);
MenuItems.displayName = "MenuItems";
export default MenuItems;
