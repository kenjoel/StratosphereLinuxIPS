class screen {
  constructor(blessed, contrib, redis_database,tree_class, timeline_class, box_class, listtable_class, gauge_class, combine_listtable_gauge_class, listbar_class) {
      this.blessed = blessed
      this.contrib = contrib
      this.tree_class = tree_class
      this.redis_database = redis_database
      this.timeline_class= timeline_class
      this.box_class = box_class
      this.listtable_class = listtable_class
      this.gauge_class = gauge_class
      this.combine_listtable_gauge_class = combine_listtable_gauge_class
      this.listbar_class = listbar_class
      this.limit_letter_outtuple = limit_letter_outtuple
      this.screen = undefined
      this.grid = undefined
      this.tree_widget = undefined
      this.timeline_widget = undefined
      this.evidence_box_widget = undefined
      this.ipinfo_widget = undefined
      this.focus_widget = undefined
      this.focus_hotkey = false
      this.current_shown_widgets = undefined
      this.tuple_widget = undefined
      this.listtable1 = undefined
      this.listtable2 = undefined
      this.gauge1 = undefined
      this.gauge2 = undefined
      this.combine_listtable_gauge = undefined
      this.helpbar = undefined
      }

    init(){
      /*
      Initialize all the widgets
      */
    	this.initScreen()
    	this.initGrid()
      this.initBoxEvidence()
      this.initTimeline()
      this.initIPInfo()
    	this.initTree()
      this.initMain()
      this.initListtableGauge()
      this.initCombine()
      this.initTuple()
      this.initListBar()
      this.initHelpTable()
      this.initHotkeys()
      this.render()
    }
    
    initScreen(){
      /*
      Initialize screen
      */
    	this.screen =this.blessed.screen()
    }

    initGrid(){
      /*
      Initialize grid
      */
    	this.grid =  new this.contrib.grid({
		  rows: 6,
		  cols: 6,
		  screen: this.screen
		});
		
    }
    initHelpTable(){
        /*
        Initialize help bar on screen
        */
        this.helptable = new this.listtable_class(this.grid, this.blessed, this.contrib, this.redis_database, this.screen, [0, 0, 5.7, 6,'help'])
        this.helptable.setHelp()
        this.helptable.hide()
    }

    initListBar(){
      /*
      Initialise help bar on screen and fill in data
      */
      this.helpbar = new this.listbar_class(this.grid, this.blessed, this.contrib, this.redis_database, this.screen)
      this.helpbar.show()
    }
    initTuple(){
      /*
      Initialize Tuple on screen and fill in data
      */
      this.tuple_widget = new this.listtable_class(this.grid, this.blessed, this.contrib, this.redis_database, this.screen, [0,0,5.7,6], this.limit_letter_outtuple)
      this.tuple_widget.hide()
    }
    initBoxEvidence(){
      /*
      Initialize evidence box on screen and fill in data
      */
      this.evidence_box_widget = new this.box_class(this.grid, this.blessed, this.contrib, this.redis_database, this.screen, [4.8,1, 0.9, 5,'Evidence'])
    }
    initTimeline(){
      /*
      Initialize timeline on screen and fill in data
      */
      this.timeline_widget = new this.timeline_class(this.grid, this.blessed, this.contrib, this.redis_database, this.screen, [0.6, 1, 4.3, 5,'Timeline',[200], true])
    }
    initIPInfo(){
      /*
      Initialize ipinfo widget on screen and fill in data
      */
      this.ipinfo_widget = new this.listtable_class(this.grid, this.blessed, this.contrib, this.redis_database, this.screen, [0, 1, 0.6, 5,'IPInfo',[30,30,10,10,10,10], false])
    }
    initListtableGauge(){
      /*
      Initialize listtable1, listtable2, gauge1, gauge2 on screen and fill in data
      */
      this.listtable1 = new this.listtable_class(this.grid, this.blessed, this.contrib, this.redis_database, this.screen, [0,0,2.8,2])
      this.listtable1.hide()
      this.listtable2 = new this.listtable_class(this.grid, this.blessed, this.contrib, this.redis_database, this.screen, [2.8,0,2.8,2])
      this.listtable2.hide()
      this.gauge1 = new this.gauge_class(this.grid, this.blessed, this.contrib, this.redis_database, this.screen, [0.3, 2, 2.6, 4])
      this.gauge1.hide()
      this.gauge2 = new this.gauge_class(this.grid, this.blessed, this.contrib, this.redis_database, this.screen, [3.1, 2, 2.6, 4])
      this.gauge2.hide()
    }

    initCombine(){
      /*
      Initialize the combination of listtable1, listtable2, gauge1, gauge2 on screen and fill in data
      */
      this.combine_listtable_gauge = new this.combine_listtable_gauge_class(this.grid, this.blessed, this.contrib, this.redis_database, this.screen, this.listtable1, this.listtable2, this.gauge1, this.gauge2)
    }

    initTree(){
      /*
      Initialize tree on screen and fill in data
      */
    	this.tree_widget = new this.tree_class(this.grid, this.blessed, this.contrib, this.redis_database, this.timeline_widget, this.screen, this.evidence_box_widget, this.ipinfo_widget)
    	this.tree_widget.getTreeDataFromDatabase() 
      this.tree_widget.focus()
      this.tree_widget.on()
      this.tree_widget.widget.style.border.fg = 'magenta'
      this.focus_widget = this.tree_widget
    }

    initMain(){
      /*
      Keep track of all main page widgets
      */
      this.mainPage = [this.tree_widget.widget, this.ipinfo_widget.widget, this.evidence_box_widget.widget, this.timeline_widget.widget]
    }

    initHotkeys(){
      /*
      Keep track of all hotkeys widgets
      */
      this.hotkeys = [this.listtable1, this.listtable2, this.gauge1, this.gauge2, this.tuple_widget, this.helptable]
    }

    e_hotkey_routine(){
      /*
      Display data for SrcPortsClient established and not established
      */
      for(var widget_idx = 0; widget_idx < this.hotkeys.length; widget_idx++){
        this.hotkeys[widget_idx].hide()
      }
      for(var widget_idx = 0; widget_idx < this.mainPage.length; widget_idx++){
            this.mainPage[widget_idx].hide()
        }
      this.tuple_widget.hide()
      this.combine_listtable_gauge.operate(
        this.tree_widget.current_ip, 
        this.tree_widget.current_tw, 
        'SrcPortsClientTCPEstablished','SrcPortsClientUDPEstablished', 'SrcPortsClientTCPNotEstablished', 'SrcPortsClientUDPNotEstablished',
        ['estSrcPortClient', 'totalflows', 'totalpkts','totalbytes'],['NotEstSrcPortClient', 'totalflows', 'totalpkts','totalbytes'])
      this.render()
      return;
    }

    d_hotkey_routine(){
      /*
      Display data for dstIPsClient established and not established
      */
      for(var widget_idx = 0; widget_idx < this.hotkeys.length; widget_idx++){
        this.hotkeys[widget_idx].hide()
      }
      for(var widget_idx = 0; widget_idx < this.mainPage.length; widget_idx++){
            this.mainPage[widget_idx].hide()
        }
      this.tuple_widget.hide()
      this.combine_listtable_gauge.operate(
      this.tree_widget.current_ip, 
      this.tree_widget.current_tw, 
      'DstIPsClientTCPEstablished','DstIPsClientUDPEstablished', 'DstIPsClientTCPNotEstablished', 'DstIPsClientUDPNotEstablished',
      ['estDstIPsClient', 'totalflows', 'totalpkts','totalbytes'],['NotEstDstIPsClient', 'totalflows', 'totalpkts','totalbytes'])
    }

    t_hotkey_routine(){
      /*
      Display data for dstPortsClient established and not established
      */
      for(var widget_idx = 0; widget_idx < this.hotkeys.length; widget_idx++){
        this.hotkeys[widget_idx].hide()
      }
      for(var widget_idx = 0; widget_idx < this.mainPage.length; widget_idx++){
            this.mainPage[widget_idx].hide()
        }
      this.tuple_widget.hide()
      this.combine_listtable_gauge.operate_IPs(
      this.tree_widget.current_ip, 
      this.tree_widget.current_tw, 
      'DstPortsClientTCPEstablished','DstPortsClientUDPEstablished', 'DstPortsClientTCPNotEstablished', 'DstPortsClientUDPNotEstablished',
      ['estDstPortClient',  'IP','Number of connections'],['NotEstDstPortClient',  'IP','Number of packets'])
    }

    r_hotkey_routine(){
      /*
      Display data for dstPortsServer established and not established
      */
      for(var widget_idx = 0; widget_idx < this.hotkeys.length; widget_idx++){
        this.hotkeys[widget_idx].hide()
      }
      for(var widget_idx = 0; widget_idx < this.mainPage.length; widget_idx++){
            this.mainPage[widget_idx].hide()
        }
      this.tuple_widget.hide()
      this.combine_listtable_gauge.operate(
      this.tree_widget.current_ip, 
      this.tree_widget.current_tw, 
      'dstPortsServerTCPEstablished','dstPortsServerUDPEstablished', 'dstPortsServerTCPNotEstablished', 'dstPortsServerUDPNotEstablished',
      ['estDstPortServer', 'totalflows', 'totalpkts','totalbytes'],['NotEstDstPortServer', 'totalflows', 'totalpkts','totalbytes'])

    }

    p_hotkey_routine(){
      /*
      Display data for DstPortsClient established and not established
      */
      for(var widget_idx = 0; widget_idx < this.hotkeys.length; widget_idx++){
        this.hotkeys[widget_idx].hide()
      }
      for(var widget_idx = 0; widget_idx < this.mainPage.length; widget_idx++){
            this.mainPage[widget_idx].hide()
        }
      this.tuple_widget.hide()
      this.combine_listtable_gauge.operate(
      this.tree_widget.current_ip, 
      this.tree_widget.current_tw, 
      'DstPortsClientTCPEstablished','DstPortsClientUDPEstablished', 'DstPortsClientTCPNotEstablished', 'DstPortsClientUDPNotEstablished',
      ['estDstPortClient',  'totalflows','totalpkts','totalbytes'],['NotEstDstPortClient',  'totalflows','totalpkts','totalbytes'])
    }

    i_hotkey_routine(){
      /*
      Function to fill and prepare the widget with out tuples  
      */
      for(var widget_idx = 0; widget_idx < this.hotkeys.length; widget_idx++){
        this.hotkeys[widget_idx].hide()
      }
      for(var widget_idx = 0; widget_idx < this.mainPage.length; widget_idx++){
          this.mainPage[widget_idx].hide()
      }
      this.gauge1.hide()
      this.gauge2.hide()
      this.listtable2.hide()
      this.listtable1.hide()
      this.tuple_widget.setOutTuples(this.tree_widget.current_ip, this.tree_widget.current_tw)
      this.tuple_widget.show()
      this.tuple_widget.focus()
      this.render()
    }
    y_hotkey_routine(){
      /*
      Function to fill and prepare the widget with in tuples  
      */
      for(var widget_idx = 0; widget_idx < this.hotkeys.length; widget_idx++){
        this.hotkeys[widget_idx].hide()
      }
      for(var widget_idx = 0; widget_idx < this.mainPage.length; widget_idx++){
        this.mainPage[widget_idx].hide()
      }
      this.gauge1.hide()
      this.gauge2.hide()
      this.listtable2.hide()
      this.listtable1.hide()
      this.tuple_widget.setInTuples(this.tree_widget.current_ip, this.tree_widget.current_tw)
      this.tuple_widget.show()
      this.tuple_widget.focus()
      this.render()
    }

    o_hotkey_routine(){
      /*
      function to update tree widget and return to main page
      */
//      for(var widget_idx = 0; widget_idx < this.hotkeys.length; widget_idx++){
//        this.hotkeys[widget_idx].hide()
//      }
//      for(var widget_idx = 0; widget_idx < this.mainPage.length; widget_idx++){
//        this.mainPage[widget_idx].show()
//      }
      this.tree_widget.getTreeDataFromDatabase()
//      this.focus_widget.focus()
//      this.focus_widget.on()
      this.render()
    }
    h_hotkey_routine(){
    for(var widget_idx = 0; widget_idx < this.hotkeys.length; widget_idx++){
        this.hotkeys[widget_idx].hide()
      }
        for(var widget_idx = 0; widget_idx < this.mainPage.length; widget_idx++){
        this.mainPage[widget_idx].hide()
      }
        this.helptable.show()
        this.render()
    }

    main_page_routine(){
      /*
      Function to go back from the hptkeys to main page of the interface
      */
      for(var widget_idx = 0; widget_idx < this.hotkeys.length; widget_idx++){
        this.hotkeys[widget_idx].hide()
      }
      for(var widget_idx = 0; widget_idx < this.mainPage.length; widget_idx++){
        this.mainPage[widget_idx].show()
      }
      this.focus_widget.focus()      
      this.render()
    }

    update_interface(){
        /*
        Function to update interface every two minutes
        */
        setInterval(this.o_hotkey_routine.bind(this), 120000)
    }
    registerEvents(){
      /*
      Function to monitor all keypresses happening on the screen
      */
      this.screen.on('keypress', (ch, key)=>{
        if(key.name == 'down' || key.name == 'j'){
          if(this.focus_hotkey){
            this.combine_listtable_gauge.down()
          }
        }
        else if(key.name == 'up' || key.name == 'k'){
          if(this.focus_hotkey){
            this.combine_listtable_gauge.up()
          }
        }
        else if(key.name == 'tab'){
          if(this.gauge1.widget.focused == true){
            this.gauge2.focus()
          }
          else if(this.gauge2.widget.focused == true){
            this.gauge1.focus()
          }
          else if(this.focus_widget == this.tree_widget){
            this.focus_widget = this.timeline_widget
            this.tree_widget.widget.style.border.fg = 'blue'
            this.timeline_widget.widget.style.border.fg='magenta'
            this.timeline_widget.widget.focus();
            this.timeline_widget.on(this.ipinfo_widget)}
          else if(this.focus_widget == this.timeline_widget){
            this.timeline_widget.widget.style.border.fg='blue'
            this.focus_widget = this.evidence_box_widget
            this.evidence_box_widget.widget.focus()}
          else{
            this.focus_widget = this.tree_widget
            this.tree_widget.widget.style.border.fg = 'magenta'
            this.tree_widget.focus();}
        		this.render()
        }	
      	else if(key.name == 'q' || key.name == "C-c"){
      		return process.exit(0);
      	}
        else if(key.name == 'escape'){
          this.helpbar.selectTab(0)
          this.main_page_routine()
          this.focus_hotkey = false
        }
        else if(key.name == 'p'){
          this.helpbar.selectTab(4)
          this.p_hotkey_routine()
          this.focus_hotkey = true
        }
        else if(key.name == 'r'){
          this.helpbar.selectTab(3)
          this.r_hotkey_routine()
          this.focus_hotkey = true
        }
        else if(key.name == 'd'){
          this.helpbar.selectTab(2)
          this.d_hotkey_routine()
          this.focus_hotkey = true
        }
        else if(key.name == 't'){
          this.helpbar.selectTab(5)
          this.t_hotkey_routine()
          this.focus_hotkey = true
        }
        else if(key.name == 'e'){
          this.helpbar.selectTab(1)
          this.e_hotkey_routine()
          this.focus_hotkey = true
        }
        else if(key.name == 'i'){
          this.helpbar.selectTab(6)
          this.i_hotkey_routine()
          this.focus_hotkey = false
        }
        else if(key.name == 'y'){
          this.helpbar.selectTab(7)
          this.y_hotkey_routine()
          this.focus_hotkey = false
        }
        else if(key.name == 'o'){
          this.helpbar.selectTab(0)
          this.o_hotkey_routine() 
          this.focus_hotkey = false
        }
        else if(key.name == 'h'){
          this.helpbar.selectTab(11)
          this.h_hotkey_routine()
          this.focus_hotkey = false
        }

      })
    }

    render(){
    	this.screen.render()
    }

}

module.exports = screen;
