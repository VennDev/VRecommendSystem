package global

import (
	svccore "github.com/venndev/vrecommendation/internal/services/types"
	lgcore "github.com/venndev/vrecommendation/pkg/logger/types"
	kfcore "github.com/venndev/vrecommendation/pkg/messaging/types"
	"github.com/venndev/vrecommendation/pkg/setting"
)

var (
	Config       setting.Config
	Logger       lgcore.Logger
	KafkaManager kfcore.KafkaManager
	EventService svccore.EventService
)
