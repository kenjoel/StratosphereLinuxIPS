const blessed = require('blessed');
const contrib = require('blessed-contrib');
const tableWidget = require('./tableWidget.js');
const treeWidget = require('./treeWidget.js');
const boxWidget = require('./boxWidget.js');
const widgets = require( './widgets.js');
class screen {
    constructor (){   //utils = new Map()
        this.screen = undefined;
        this.grid = undefined;
 
    }
init(){
    this.screen = blessed.screen({
        title:'without name'
    })
    this.grid = new contrib.grid({rows:6, cols:6, screen: this.screen})
}

initScreen(){
    var table = new tableWidget({blessed, contrib, screen: this.screen, grid:{ gridObj:this.grid, gridLayout:[0, 1, 2.5, 5]}});
    var tree = new widgets.WidgetTree({blessed, contrib, screen: this.screen, grid:{ gridObj:this.grid, gridLayout:[0,0,5,1]}});
    var box = new widgets.WidgetBox({blessed, contrib, screen: this.screen, grid:{ gridObj:this.grid, gridLayout:[5, 0, 0.4, 6]}})

    this.screen.render();
}

     
exitKey(){
    this.screen.key(["escape", "q", "C-c"], function(ch, key) {
    return process.exit(0);
})}
}

var c = new screen();
c.init();
c.initScreen();
c.exitKey();


