import React, { Component } from 'react';
import io from 'socket.io-client';
import Fade from '@mui/material/Fade';
import Clock from './components/Clock';
import CustomAvatar from './components/Avatar';

import './App.css';
import './animations.css';

const assistantSocket = io({path: "/assistant"});
const videoSocket = io({path: "/video"});

export default class App extends Component {

    constructor(props) {
        super(props);
        this.state = {
            transcript: "",
            graphic_response: "",
            assistant_state: "idle",
            avatar: {
                avatarStyle: 'Circle',
                topType: 'ShortHairShortFlat',
                accessoriesType: 'Blank',
                hairColor: 'Black',
                facialHairType: 'Blank',
                clotheType: 'ShirtCrewNeck',
                clotheColor: 'PastelBlue',
                eyeType: 'Default',
                eyebrowType: 'Default',
                mouthType: 'Serious',
                skinColor: 'Light'
            },
            emotion: null,
            name: null,
            voice_analysis: null,
            google_timeout: 0,
            user_timeout: 0,
            greetings_timeout: 0,
            day_overview: false,
            day_overview_hash: 0
             
        }
    };

    componentDidMount() {
        document.title = "SmartMirror";
        // socket.emit("getData", "home")

        assistantSocket.on("graphic_response", (data) => {
            if (data.includes("Resoconto giornaliero")) {
                this.setState({day_overview_hash: Date.now()})
                this.setState({day_overview: true})
            }
            this.setState({ graphic_response: data});
            this.setState({ google_timeout: 30 })
        });

        assistantSocket.on("transcript", (data) => {
            if(this.state.assistant_state === 'listening') {
                this.setState({ transcript: data });
            }
            
        });

        assistantSocket.on("assistant_state", (data) => {
            this.setState({ assistant_state: data });
            if(this.state.assistant_state !== 'listening') {
                this.setState({ transcript: "" });
            }
            else {
                this.setState({day_overview: false})
            }
        });


        assistantSocket.on("voice_analysis", (data) => {
            this.setState({ voice_analysis: data });
            if (data.user_pred === this.state.name) {
                this.setState({
                    user_timeout: 7
                });
            }
        });


        videoSocket.on("user_data", (data) => {
            if (data !== undefined) {
                if (data.user.name !== 'Guest')  {
                    if (this.state.name !== data.user.name) {
                        this.setState({
                            greetings_timeout: 3,
                            google_timeout: 0
                        });
                    }


                    this.setState({ user_timeout: 7 })
                    this.setState({
                        emotion: data.emo,
                        name: data.user.name
                    });
                }
                else {
                    if (this.state.user_timeout === 0) {
                        this.setState({
                            emotion: data.emo,
                            name: data.user.name,
                            google_timeout: 0
                        });
                    }
                }
                if (data.avatar) {
                    this.setState({
                        avatar: data.avatar,
                    });
                    console.log(data.avatar)
                }
            }
            else {
                if (this.state.user_timeout === 0) {
                    this.setState({
                        emotion: null,
                        name: null,
                        google_timeout: 0
                    });
                }
            }
        });

        this.interval = setInterval(() => this.updateTimer(), 1000);
    }

    updateTimer() {
        // Google GUI timeout
        var google_timeout = this.state.google_timeout
        
        if (google_timeout > 0) {
            this.setState({ google_timeout: google_timeout - 1 })
        }

        if (google_timeout === 0) {
            this.setState({day_overview: false})
        }

        // User detected timeout
        var user_timeout = this.state.user_timeout
        if (user_timeout > 0) {
            this.setState({ user_timeout: user_timeout - 1 })
        }

        var greetings_timeout = this.state.greetings_timeout
        if (greetings_timeout > 0) {
            this.setState({ greetings_timeout: greetings_timeout - 1 })
        }
    }

    componentWillUnmount() {
        clearInterval(this.interval);
    }

    render() {
        return (
            // 
                <div>
                    <Fade in={this.state.greetings_timeout === 0 && this.state.name !== null}>
                        <div id='top_left'>
                            <Clock/>
                        </div>
                    </Fade>

                    <Fade in={this.state.name !== "Guest" && this.state.name !== null && this.state.greetings_timeout === 0}>
                        <div id='top_right'>
                            <CustomAvatar
                                avatar={this.state.avatar}
                                name={this.state.name}
                                emotion={this.state.emotion}
                            />
                        </div>
                    </Fade>
                    <Fade in={this.state.name === "Guest" && this.state.name !== null}>
                        <div id='top_right'>
                            <div id='welcome_message'>Ciao! Prova a dire: "Smart Mirror, registra utente" e il tuo nome.</div>
                        </div>
                    </Fade>

                    <Fade in={this.state.transcript !== '' && this.state.greetings_timeout === 0}>
                        <div id='transcript'>{this.state.transcript}</div>
                    </Fade>

                    <Fade in={this.state.greetings_timeout !== 0}>
                        <div id='greetings'>Ciao {this.state.name}!</div>
                    </Fade>


                    <Fade in={this.state.day_overview}>
                        <img id='day_overview' src={process.env.REACT_APP_SERVER_URL + ':5555/day_overview.png?' + this.state.day_overview_hash}></img>
                    </Fade>

                    <Fade in={this.state.greetings_timeout === 0}>
                        <div id = "canvas" className = { this.state.assistant_state } >
                            <div className = "dot blue" />
                            <div className = "dot red" />
                            <div className = "dot yellow" />
                            <div className = "dot green" />
                        </div>
                    </Fade>

                    <Fade in={this.state.name !== null && this.state.google_timeout !== 0  && this.state.greetings_timeout === 0}>
                        <div>
                            <div dangerouslySetInnerHTML = {{ __html: this.state.graphic_response }} />
                        </div>
                    </Fade>
                
                </div>
        )
    }
}