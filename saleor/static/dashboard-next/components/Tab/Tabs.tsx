import * as React from "react";

export interface TabsProps {
  children: (
    props: {
      changeTab: (index: number) => void;
      currentTab: number;
    }
  ) => React.ReactNode;
}

interface TabsState {
  currentTab: number;
}

class Tabs extends React.Component<TabsProps, TabsState> {
  state: TabsState = {
    currentTab: 0
  };

  changeTab = (index: number) => this.setState({ currentTab: index });

  render() {
    return this.props.children({
      changeTab: this.changeTab,
      currentTab: this.state.currentTab
    });
  }
}

export default Tabs;
