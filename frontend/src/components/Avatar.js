import Avatar from 'avataaars'

function CustomAvatar(props) {
    // neutral, happiness, sadness, surprise, fear, disgust, anger, contempt, uncertain

    var mouthType = props.avatar.mouthType
    var eyeType = props.avatar.eyeType
    var eyebrowType = props.avatar.eyebrowType

    switch (props.emotion) {
        case 'happy':
            mouthType = 'Smile'
            eyeType = 'Happy'
            break;
    
        case 'angry':
            eyebrowType = 'AngryNatural'
            break;

        case 'surprised':
            eyebrowType = 'RaisedExcitedNatural'
            mouthType = 'Disbelief'
            break;

        case 'sad':
            eyebrowType = 'SadConcernedNatural'
            mouthType = 'Sad'
            eyeType = 'Cry'
            break;

        case 'disgusted':
            eyebrowType = 'SadConcernedNatural'
            mouthType = 'Eating'
            break;

        case 'pensive':
            eyebrowType = 'FlatNatural'
            break;

        case 'feared':
            eyebrowType = 'SadConcernedNatural'
            mouthType = 'ScreamOpen'
            break;

        case 'uncertain':
            eyebrowType = 'UpDown'
            break;
    
        default:
            break;
    }

    return (
        <div>
            <Avatar
                style={{ width: '250px', height: '250px' }}
                avatarStyle={props.avatar.avatarStyle}
                topType={props.avatar.topType}
                accessoriesType={props.avatar.accessoriesType}
                hairColor={props.avatar.hairColor}
                facialHairType={props.avatar.facialHairType}
                clotheType={props.avatar.clotheType}
                clotheColor={props.avatar.clotheColor}
                eyeType={eyeType}
                eyebrowType={eyebrowType}
                mouthType={mouthType}
                skinColor={props.avatar.skinColor}
            />
            <div id='avatar_name'>{props.name}</div>
        </div>
    )
}
export default CustomAvatar;



