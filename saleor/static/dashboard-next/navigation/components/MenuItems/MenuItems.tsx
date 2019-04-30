import Card from "@material-ui/core/Card";
import Paper from "@material-ui/core/Paper";
import {
  createStyles,
  Theme,
  withStyles,
  WithStyles
} from "@material-ui/core/styles";
import Typography from "@material-ui/core/Typography";
import classNames from "classnames";
import * as React from "react";
import SortableTree, { NodeRendererProps } from "react-sortable-tree";

import CardTitle from "../../../components/CardTitle";
import useTheme from "../../../hooks/useTheme";
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
    darkRoot: {
      background: `${theme.palette.grey[800]} !important`
    },
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
      transition: `margin ${theme.transitions.duration.standard}ms`
    }
  });

class Node extends React.Component<NodeRendererProps> {
  render() {
    return <NodeComponent {...this.props} />;
  }
}

const NodeComponent = withStyles(styles, {
  name: "NodeComponent"
})(
  ({
    classes,
    node,
    path,
    connectDragPreview,
    connectDragSource
  }: NodeRendererProps & WithStyles<typeof styles>) =>
    connectDragPreview(
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
    )
);

const MenuItems = withStyles(styles, { name: "MenuItems" })(
  ({
    classes,
    items,
    onChange
  }: MenuItemsProps & WithStyles<typeof styles>) => {
    const { isDark } = useTheme();

    return (
      <Card>
        <CardTitle title={i18n.t("Menu Items")} />
        <div style={{ height: getNodeQuantity(items) * NODE_HEIGHT }}>
          <SortableTree
            className={classNames(classes.root, {
              [classes.darkRoot]: isDark
            })}
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
              nodeContentRenderer: Node
            }}
            onChange={newTree =>
              onChange(getDiff(items.map(getNodeData), newTree as TreeNode[]))
            }
          />
        </div>
      </Card>
    );
  }
);
MenuItems.displayName = "MenuItems";
export default MenuItems;
