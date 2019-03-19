import Button from "@material-ui/core/Button";
import IconButton from "@material-ui/core/IconButton";
import Snackbar from "@material-ui/core/Snackbar";
import CloseIcon from "@material-ui/icons/Close";
import * as React from "react";

import { IMessage, MessageContext } from "./";

interface Message extends IMessage {
  key: string;
}
interface MessageManagerState {
  message: Message;
  opened: boolean;
}

export class MessageManager extends React.Component<{}, MessageManagerState> {
  state = {
    message: { text: "", key: "0", onUndo: undefined },
    opened: false
  };
  queue = [];

  handleClose = (_, reason) => {
    if (reason === "clickaway") {
      return;
    }
    this.setState({ opened: false });
  };

  handleExited = () => {
    this.processQueue();
  };

  pushMessage = (message: IMessage) => {
    this.queue.push({
      key: new Date().getTime(),
      ...message
    });

    if (this.state.opened) {
      this.setState({ opened: false });
    } else {
      this.processQueue();
    }
  };

  processQueue = () => {
    if (this.queue.length > 0) {
      this.setState({
        message: this.queue.shift(),
        opened: true
      });
    }
  };

  render() {
    const { text, key, onUndo } = this.state.message;
    return (
      <>
        <Snackbar
          key={key}
          anchorOrigin={{
            horizontal: "right",
            vertical: "top"
          }}
          open={this.state.opened}
          autoHideDuration={3000}
          onClose={this.handleClose}
          onExited={this.handleExited}
          ContentProps={{
            "aria-describedby": "message-id"
          }}
          message={<span id="message-id">{text}</span>}
          action={[
            !!onUndo ? (
              <Button
                key="undo"
                color="secondary"
                size="small"
                onClick={this.handleClose as any}
              >
                UNDO
              </Button>
            ) : (
              undefined
            ),
            <IconButton
              key="close"
              aria-label="Close"
              color="inherit"
              onClick={this.handleClose as any}
            >
              <CloseIcon />
            </IconButton>
          ]}
        />
        <MessageContext.Provider value={this.pushMessage}>
          {this.props.children}
        </MessageContext.Provider>
      </>
    );
  }
}
export default MessageManager;
